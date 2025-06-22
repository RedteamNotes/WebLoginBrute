#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import yaml
import re
import socket
import ssl
from typing import Any, Dict, Optional, List, Union
from urllib.parse import urlparse
from pydantic import BaseModel, Field, validator, ValidationError, root_validator, model_validator
from .exceptions import ConfigurationError, ValidationError as ConfigValidationError, SecurityError
from .version import __version__, get_version_info

# 使用统一的版本管理
version = __version__

class Config(BaseModel):
    """
    统一管理所有配置项，支持命令行和YAML配置文件，基于pydantic自动类型和范围校验。
    增强的验证机制包括：URL格式验证、文件存在性检查、网络连通性测试、安全策略验证等。
    """
    url: str = Field(..., description="登录表单页面URL")
    action: str = Field(..., description="登录表单提交URL")
    users: str = Field(..., description="用户名字典文件")
    passwords: str = Field(..., description="密码字典文件")
    csrf: Optional[str] = Field(None, description="CSRF token字段名")
    login_field: Optional[str] = None
    login_value: Optional[str] = None
    cookie: Optional[str] = None
    timeout: int = Field(30, ge=1, le=600, description="请求超时时间（秒）")
    threads: int = Field(5, ge=1, le=100, description="并发线程数")
    resume: bool = False
    log: str = Field('bruteforce_progress.json', description="进度文件路径")
    aggressive: int = Field(1, ge=0, le=3, description="对抗级别: 0(静默) 1(标准) 2(激进) 3(极限)")
    dry_run: bool = False
    verbose: bool = False
    
    # 内存管理配置
    max_memory_mb: int = Field(500, ge=100, le=2000, description="最大内存使用量(MB)")
    memory_warning_threshold: float = Field(0.8, ge=0.5, le=0.95, description="内存警告阈值")
    memory_critical_threshold: float = Field(0.9, ge=0.7, le=0.99, description="内存临界阈值")
    memory_cleanup_interval: int = Field(60, ge=30, le=300, description="内存清理间隔(秒)")
    
    # 会话管理配置
    session_rotation_interval: int = Field(300, ge=60, le=1800, description="会话轮换间隔(秒)")
    session_lifetime: int = Field(600, ge=300, le=3600, description="会话生命周期(秒)")
    max_session_pool_size: int = Field(100, ge=10, le=500, description="最大会话池大小")
    enable_session_rotation: bool = Field(True, description="是否启用会话轮换")
    rotation_strategy: str = Field("time", description="轮换策略")
    
    # 新增：健康检查和验证配置
    enable_health_check: bool = Field(True, description="是否启用健康检查")
    validate_network_connectivity: bool = Field(True, description="是否验证网络连通性")
    validate_file_integrity: bool = Field(True, description="是否验证文件完整性")
    max_file_size_mb: int = Field(100, ge=1, le=1000, description="最大文件大小(MB)")
    allowed_domains: Optional[List[str]] = Field(None, description="允许的域名白名单")
    blocked_domains: Optional[List[str]] = Field(None, description="阻止的域名黑名单")
    security_level: str = Field("standard", description="安全级别: low, standard, high, paranoid")

    class Config:
        """Pydantic配置"""
        validate_assignment = True
        extra = "forbid"  # 禁止额外字段
        use_enum_values = True

    @classmethod
    def from_args_and_yaml(cls) -> 'Config':
        """从命令行参数和YAML配置文件创建配置对象"""
        args, defaults = cls.parse_args()
        config_path = args.config
        file_config = {}
        
        if config_path:
            if not os.path.exists(config_path):
                raise ConfigurationError(f"配置文件不存在: {config_path}", config_path=config_path)
            
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                raise ConfigurationError(f"YAML配置文件格式错误: {e}", config_path=config_path)
            except Exception as e:
                raise ConfigurationError(f"读取配置文件失败: {e}", config_path=config_path)
        
        # 合并配置：文件配置 + 命令行参数
        final_config = file_config.copy()
        for key, value in vars(args).items():
            if key != 'config' and value is not None and value != defaults.get(key):
                final_config[key] = value
        
        try:
            config = cls.parse_obj(final_config)
            
            # 执行健康检查
            if config.enable_health_check:
                config._perform_health_checks()
            
            import logging
            logging.debug(f"最终生效配置: {config.dict()}")
            return config
            
        except ValidationError as e:
            invalid_fields = [str(err['loc'][0]) for err in e.errors()]
            raise ConfigurationError(
                f"配置参数校验失败: {e}", 
                config_path=config_path,
                invalid_fields=invalid_fields
            )

    @staticmethod
    def parse_args() -> tuple:
        """解析命令行参数"""
        parser = argparse.ArgumentParser(
            description="WebLoginBrute 配置",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
示例用法:
  %(prog)s -u https://example.com/login -a https://example.com/auth -U users.txt -P passwords.txt
  %(prog)s --config config.yaml --verbose
  %(prog)s -u https://example.com/login -t 10 --aggressive 2 --dry-run
            """
        )
        
        # 基础参数
        parser.add_argument('--config', help='YAML配置文件路径，可选')
        parser.add_argument('-u', '--url', help='登录表单页面URL')
        parser.add_argument('-a', '--action', help='登录表单提交URL')
        parser.add_argument('-U', '--users', help='用户名字典文件')
        parser.add_argument('-P', '--passwords', help='密码字典文件')
        parser.add_argument('-s', '--csrf', help='CSRF token字段名')
        parser.add_argument('-f', '--login-field', help='额外的登录字段名')
        parser.add_argument('-v', '--login-value', help='额外的登录字段值')
        parser.add_argument('-c', '--cookie', help='Cookie文件路径')
        parser.add_argument('-T', '--timeout', type=int, help='请求超时时间（秒）')
        parser.add_argument('-t', '--threads', type=int, help='并发线程数')
        parser.add_argument('-r', '--resume', action='store_true', help='从上次中断的地方继续')
        parser.add_argument('-l', '--log', help='进度文件路径')
        parser.add_argument('-A', '--aggressive', type=int, choices=[0, 1, 2, 3], help='对抗级别: 0(静默) 1(标准) 2(激进) 3(极限)')
        parser.add_argument('--dry-run', action='store_true', help='测试模式，不实际发送请求')
        parser.add_argument('--verbose', action='store_true', help='详细输出')
        parser.add_argument('-V', '--version', action='version', version=f'%(prog)s {version}')
        
        # 内存管理参数
        parser.add_argument('--max-memory', type=int, help='最大内存使用量(MB)')
        parser.add_argument('--memory-warning-threshold', type=float, help='内存警告阈值')
        parser.add_argument('--memory-critical-threshold', type=float, help='内存临界阈值')
        parser.add_argument('--memory-cleanup-interval', type=int, help='内存清理间隔(秒)')
        
        # 会话管理参数
        parser.add_argument('--session-rotation-interval', type=int, help='会话轮换间隔(秒)')
        parser.add_argument('--session-lifetime', type=int, help='会话生命周期(秒)')
        parser.add_argument('--max-session-pool-size', type=int, help='最大会话池大小')
        parser.add_argument('--disable-session-rotation', action='store_true', help='禁用会话轮换')
        parser.add_argument('--rotation-strategy', choices=['time', 'request_count', 'error_rate'], help='轮换策略')
        
        # 健康检查和验证参数
        parser.add_argument('--disable-health-check', action='store_true', help='禁用健康检查')
        parser.add_argument('--disable-network-validation', action='store_true', help='禁用网络连通性验证')
        parser.add_argument('--disable-file-validation', action='store_true', help='禁用文件完整性验证')
        parser.add_argument('--max-file-size', type=int, help='最大文件大小(MB)')
        parser.add_argument('--security-level', choices=['low', 'standard', 'high', 'paranoid'], help='安全级别')
        
        # 参数别名映射，提升兼容性
        parser.add_argument('--form-url', dest='url', help='登录表单页面URL (别名)')
        parser.add_argument('--submit-url', dest='action', help='登录表单提交URL (别名)')
        parser.add_argument('--username-file', dest='users', help='用户名字典文件 (别名)')
        parser.add_argument('--password-file', dest='passwords', help='密码字典文件 (别名)')
        parser.add_argument('--csrf-field', dest='csrf', help='CSRF token字段名 (别名)')
        parser.add_argument('--cookie-file', dest='cookie', help='Cookie文件路径 (别名)')
        parser.add_argument('--progress-file', dest='log', help='进度文件路径 (别名)')
        parser.add_argument('--aggression-level', dest='aggressive', type=int, choices=[0, 1, 2, 3], help='对抗级别: 0(静默) 1(标准) 2(激进) 3(极限) (别名)')
        
        defaults = {opt.dest: opt.default for opt in parser._actions}
        args = parser.parse_args()
        
        # 处理禁用会话轮换的参数
        if hasattr(args, 'disable_session_rotation') and args.disable_session_rotation:
            args.enable_session_rotation = False
        
        # 处理健康检查参数
        if hasattr(args, 'disable_health_check') and args.disable_health_check:
            args.enable_health_check = False
        if hasattr(args, 'disable_network_validation') and args.disable_network_validation:
            args.validate_network_connectivity = False
        if hasattr(args, 'disable_file_validation') and args.disable_file_validation:
            args.validate_file_integrity = False
        
        return args, defaults

    # 基础验证器
    @validator('url', 'action', pre=True, always=True)
    def url_must_be_http(cls, v):
        """验证URL格式和安全性"""
        if not v:
            return v
            
        if not (v.startswith('http://') or v.startswith('https://')):
            raise ConfigValidationError('URL必须以http://或https://开头', field_name='url', field_value=v)
        
        if len(v) > 2048:
            raise ConfigValidationError('URL过长', field_name='url', field_value=v)
        
        # 验证URL格式
        try:
            parsed = urlparse(v)
            if not parsed.hostname:
                raise ConfigValidationError('URL格式无效', field_name='url', field_value=v)
        except Exception:
            raise ConfigValidationError('URL格式无效', field_name='url', field_value=v)
        
        return v

    @validator('users', 'passwords', pre=True, always=True)
    def required_file_must_exist(cls, v):
        """验证必需文件存在性"""
        if not v:
            return v
            
        if not os.path.exists(v):
            raise ConfigValidationError(f'必需文件不存在: {v}', field_name='users' if 'users' in str(cls) else 'passwords', field_value=v)
        
        if len(v) > 256:
            raise ConfigValidationError('文件路径过长', field_name='users' if 'users' in str(cls) else 'passwords', field_value=v)
        
        return v

    @validator('cookie', pre=True, always=True)
    def optional_file_must_exist_if_provided(cls, v):
        """验证可选文件存在性"""
        if not v:
            return v
            
        if not os.path.exists(v):
            raise ConfigValidationError(f'可选文件不存在: {v}', field_name='cookie', field_value=v)
        
        if len(v) > 256:
            raise ConfigValidationError('文件路径过长', field_name='cookie', field_value=v)
        
        return v

    @validator('login_field', 'login_value', pre=True, always=True)
    def login_field_value_length(cls, v):
        """验证登录字段长度"""
        if v and len(v) > 128:
            raise ConfigValidationError('字段值过长', field_name='login_field' if 'login_field' in str(cls) else 'login_value', field_value=v)
        return v

    @validator('csrf', pre=True, always=True)
    def csrf_length(cls, v):
        """验证CSRF字段长度"""
        if v and len(v) > 128:
            raise ConfigValidationError('CSRF字段名过长', field_name='csrf', field_value=v)
        return v

    @validator('rotation_strategy', pre=True, always=True)
    def validate_rotation_strategy(cls, v):
        """验证轮换策略"""
        valid_strategies = ['time', 'request_count', 'error_rate']
        if v not in valid_strategies:
            raise ConfigValidationError(f'无效的轮换策略: {v}', field_name='rotation_strategy', field_value=v, validation_rule=f'必须是以下之一: {valid_strategies}')
        return v

    @validator('security_level', pre=True, always=True)
    def validate_security_level(cls, v):
        """验证安全级别"""
        valid_levels = ['low', 'standard', 'high', 'paranoid']
        if v not in valid_levels:
            raise ConfigValidationError(f'无效的安全级别: {v}', field_name='security_level', field_value=v, validation_rule=f'必须是以下之一: {valid_levels}')
        return v

    # 根验证器
    @model_validator(mode='after')
    def validate_config_consistency(self):
        """验证配置一致性"""
        # 检查内存阈值配置
        warning_threshold = self.memory_warning_threshold
        critical_threshold = self.memory_critical_threshold
        
        if warning_threshold >= critical_threshold:
            raise ConfigValidationError(
                '内存警告阈值必须小于临界阈值',
                field_name='memory_thresholds',
                field_value=f'warning={warning_threshold}, critical={critical_threshold}'
            )
        
        # 检查会话配置
        rotation_interval = self.session_rotation_interval
        session_lifetime = self.session_lifetime
        
        if rotation_interval >= session_lifetime:
            raise ConfigValidationError(
                '会话轮换间隔必须小于会话生命周期',
                field_name='session_timing',
                field_value=f'rotation={rotation_interval}, lifetime={session_lifetime}'
            )
        
        return self

    def _perform_health_checks(self):
        """执行健康检查"""
        import logging
        
        logging.info("开始执行配置健康检查...")
        
        # 1. 网络连通性检查
        if self.validate_network_connectivity:
            self._check_network_connectivity()
        
        # 2. 文件完整性检查
        if self.validate_file_integrity:
            self._check_file_integrity()
        
        # 3. 安全策略检查
        self._check_security_policies()
        
        # 4. 系统资源检查
        self._check_system_resources()
        
        logging.info("配置健康检查完成")

    def _check_network_connectivity(self):
        """检查网络连通性"""
        import logging
        import socket
        import requests
        
        logging.info("检查网络连通性...")
        
        urls_to_check = [self.url, self.action]
        
        for url in urls_to_check:
            try:
                parsed = urlparse(url)
                hostname = parsed.hostname
                if not hostname:
                    raise ConfigurationError(f"无效的URL: {url}")
                    
                port = parsed.port or (443 if parsed.scheme == 'https' else 80)
                
                # DNS解析检查
                try:
                    ip = socket.gethostbyname(hostname)
                    logging.debug(f"DNS解析成功: {hostname} -> {ip}")
                except socket.gaierror as e:
                    raise ConfigurationError(f"DNS解析失败: {hostname}")
                
                # 端口连通性检查
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(10)
                    result = sock.connect_ex((hostname, port))
                    sock.close()
                    
                    if result != 0:
                        raise ConfigurationError(f"端口连通性检查失败: {hostname}:{port}")
                    
                    logging.debug(f"端口连通性检查成功: {hostname}:{port}")
                    
                except Exception as e:
                    raise ConfigurationError(f"端口连通性检查异常: {hostname}:{port}")
                
                # HTTP响应检查（可选）
                if not self.dry_run:
                    try:
                        response = requests.head(url, timeout=10, allow_redirects=True)
                        logging.debug(f"HTTP响应检查成功: {url} -> {response.status_code}")
                    except Exception as e:
                        logging.warning(f"HTTP响应检查失败: {url} - {e}")
                
            except Exception as e:
                if isinstance(e, ConfigurationError):
                    raise
                raise ConfigurationError(f"网络连通性检查失败: {url}")

    def _check_file_integrity(self):
        """检查文件完整性"""
        import logging
        import hashlib
        
        logging.info("检查文件完整性...")
        
        files_to_check = [self.users, self.passwords]
        if self.cookie:
            files_to_check.append(self.cookie)
        
        for file_path in files_to_check:
            try:
                # 检查文件大小
                file_size = os.path.getsize(file_path)
                max_size = self.max_file_size_mb * 1024 * 1024
                
                if file_size > max_size:
                    raise ConfigurationError(
                        f"文件过大: {file_path} ({file_size / 1024 / 1024:.1f}MB > {self.max_file_size_mb}MB)"
                    )
                
                # 检查文件可读性
                with open(file_path, 'r', encoding='utf-8') as f:
                    # 读取前几行检查格式
                    for i, line in enumerate(f):
                        if i >= 10:  # 只检查前10行
                            break
                        if len(line.strip()) > 1000:  # 单行过长
                            raise ConfigurationError(
                                f"文件格式异常: {file_path} 第{i+1}行过长"
                            )
                
                logging.debug(f"文件完整性检查通过: {file_path}")
                
            except Exception as e:
                if isinstance(e, ConfigurationError):
                    raise
                raise ConfigurationError(f"文件完整性检查失败: {file_path}")

    def _check_security_policies(self):
        """检查安全策略"""
        import logging
        
        logging.info("检查安全策略...")
        
        # 检查域名白名单/黑名单
        if self.allowed_domains or self.blocked_domains:
            urls_to_check = [self.url, self.action]
            
            for url in urls_to_check:
                parsed = urlparse(url)
                hostname = parsed.hostname
                
                # 检查黑名单
                if self.blocked_domains and hostname in self.blocked_domains:
                    raise SecurityError(
                        f"目标域名在黑名单中: {hostname}",
                        security_check="domain_blacklist",
                        threat_level="HIGH"
                    )
                
                # 检查白名单
                if self.allowed_domains and hostname not in self.allowed_domains:
                    raise SecurityError(
                        f"目标域名不在白名单中: {hostname}",
                        security_check="domain_whitelist",
                        threat_level="HIGH"
                    )
        
        # 根据安全级别调整配置
        if self.security_level == "paranoid":
            # 偏执模式：最严格的安全设置
            if self.threads > 5:
                logging.warning("偏执模式下线程数已自动调整为5")
                self.threads = 5
            
            if self.timeout < 60:
                logging.warning("偏执模式下超时时间已自动调整为60秒")
                self.timeout = 60
        
        elif self.security_level == "high":
            # 高安全模式
            if self.threads > 10:
                logging.warning("高安全模式下线程数已自动调整为10")
                self.threads = 10
        
        logging.debug("安全策略检查完成")

    def _check_system_resources(self):
        """检查系统资源"""
        import logging
        
        logging.info("检查系统资源...")
        
        try:
            import psutil
            
            # 检查可用内存
            memory = psutil.virtual_memory()
            available_memory_mb = memory.available / 1024 / 1024
            
            if available_memory_mb < self.max_memory_mb:
                logging.warning(f"可用内存不足: {available_memory_mb:.1f}MB < {self.max_memory_mb}MB")
            
            # 检查CPU核心数
            cpu_count = psutil.cpu_count()
            if cpu_count and self.threads > cpu_count * 2:
                logging.warning(f"线程数可能过多: {self.threads} > {cpu_count * 2}")
            
            # 检查磁盘空间
            disk = psutil.disk_usage('.')
            free_space_mb = disk.free / 1024 / 1024
            
            if free_space_mb < 100:  # 至少需要100MB
                logging.warning(f"磁盘空间不足: {free_space_mb:.1f}MB")
            
            logging.debug("系统资源检查完成")
            
        except ImportError:
            logging.warning("psutil不可用，跳过系统资源检查")
        except Exception as e:
            logging.warning(f"系统资源检查失败: {e}")

    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        return {
            'version': version,
            'url': self.url,
            'action': self.action,
            'threads': self.threads,
            'timeout': self.timeout,
            'aggressive': self.aggressive,
            'security_level': self.security_level,
            'enable_health_check': self.enable_health_check,
            'max_memory_mb': self.max_memory_mb,
            'enable_session_rotation': self.enable_session_rotation
        }

    def validate_runtime(self) -> bool:
        """运行时验证"""
        try:
            # 重新执行关键检查
            if self.validate_network_connectivity:
                self._check_network_connectivity()
            
            if self.validate_file_integrity:
                self._check_file_integrity()
            
            return True
        except Exception as e:
            import logging
            logging.error(f"运行时验证失败: {e}")
            return False
