from flask import Blueprint, request, jsonify, render_template
from flask_admin.contrib.sqla import ModelView
from flask_admin import expose
from . import db
from .models import User
import uuid

user_bp = Blueprint('user_management', __name__, url_prefix='/admin/user')

# 多租户数据隔离 - 假设通过tenant_id字段实现
# 这里简化处理，实际项目中可以通过请求上下文或JWT获取当前租户
current_tenant_id = 'default-tenant'

# 动态用户属性模板 - 可以从数据库或配置中加载
user_attribute_templates = {
    'default': ['first_name', 'last_name', 'email', 'phone_number', 'phone', 'address'],
    'extended': ['first_name', 'last_name', 'email', 'phone_number', 'phone', 'address', 'website', 'ip_address', 'currency', 'timezone']
}

# 字段级权限控制 - 基于用户角色
field_permissions = {
    'admin': ['*'],  # 所有字段都可访问
    'editor': ['first_name', 'last_name', 'email', 'phone_number', 'phone', 'address'],
    'viewer': ['first_name', 'last_name', 'email', 'phone_number', 'phone', 'address']
}

# 操作审计日志
audit_logs = []

def log_audit(action, user_id, details):
    """记录操作审计日志"""
    audit_logs.append({
        'id': str(uuid.uuid4()),
        'action': action,
        'user_id': user_id,
        'details': details,
        'timestamp': db.func.now()
    })

class UserManagementView(ModelView):
    """用户管理视图，实现微前端架构下的用户管理"""
    
    @expose('/')
    def index(self):
        """用户管理主页面"""
        return render_template('admin/user_management.html')
    
    @expose('/api/users', methods=['GET'])
    def api_users(self):
        """API: 获取用户列表，支持游标分页"""
        # 解析请求参数
        cursor = request.args.get('cursor', None)
        limit = int(request.args.get('limit', 100))  # 虚拟滚动建议每次加载100条
        template = request.args.get('template', 'default')
        role = request.args.get('role', 'admin')
        
        # 多租户数据隔离
        query = User.query.filter_by(tenant_id=current_tenant_id)
        
        # 游标分页
        if cursor:
            query = query.filter(User.id > cursor)
        
        # 获取字段权限
        allowed_fields = field_permissions.get(role, [])
        
        # 执行查询
        users = query.order_by(User.id).limit(limit + 1).all()
        
        # 处理游标
        has_more = len(users) > limit
        next_cursor = users[-1].id if has_more else None
        users = users[:limit] if has_more else users
        
        # 动态属性模板和字段权限过滤
        user_list = []
        for user in users:
            user_data = {}
            attributes = user_attribute_templates.get(template, [])
            for attr in attributes:
                if allowed_fields == ['*'] or attr in allowed_fields:
                    user_data[attr] = getattr(user, attr)
            user_list.append(user_data)
        
        return jsonify({
            'users': user_list,
            'next_cursor': str(next_cursor) if next_cursor else None,
            'has_more': has_more
        })
    
    @expose('/api/users/<user_id>', methods=['GET'])
    def api_user_detail(self, user_id):
        """API: 获取用户详细信息"""
        role = request.args.get('role', 'admin')
        allowed_fields = field_permissions.get(role, [])
        
        user = User.query.filter_by(id=user_id, tenant_id=current_tenant_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user_data = {}
        for attr in dir(user):
            if not attr.startswith('_') and (allowed_fields == ['*'] or attr in allowed_fields):
                try:
                    value = getattr(user, attr)
                    if not callable(value):
                        user_data[attr] = value
                except:
                    pass
        
        return jsonify(user_data)
    
    @expose('/api/users', methods=['POST'])
    def api_create_user(self):
        """API: 创建用户"""
        data = request.json
        
        # 多租户数据隔离
        data['tenant_id'] = current_tenant_id
        
        # 字段权限检查
        role = request.args.get('role', 'admin')
        allowed_fields = field_permissions.get(role, [])
        
        if allowed_fields != ['*']:
            filtered_data = {k: v for k, v in data.items() if k in allowed_fields}
        else:
            filtered_data = data
        
        # 创建用户
        user = User(**filtered_data)
        db.session.add(user)
        db.session.commit()
        
        # 记录审计日志
        log_audit('create_user', user.id, {'data': filtered_data})
        
        return jsonify({'id': str(user.id)}), 201
    
    @expose('/api/users/<user_id>', methods=['PUT'])
    def api_update_user(self, user_id):
        """API: 更新用户"""
        data = request.json
        
        user = User.query.filter_by(id=user_id, tenant_id=current_tenant_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # 字段权限检查
        role = request.args.get('role', 'admin')
        allowed_fields = field_permissions.get(role, [])
        
        if allowed_fields != ['*']:
            filtered_data = {k: v for k, v in data.items() if k in allowed_fields}
        else:
            filtered_data = data
        
        # 更新用户
        for key, value in filtered_data.items():
            setattr(user, key, value)
        
        db.session.commit()
        
        # 记录审计日志
        log_audit('update_user', user.id, {'data': filtered_data})
        
        return jsonify({'success': True})
    
    @expose('/api/users/<user_id>', methods=['DELETE'])
    def api_delete_user(self, user_id):
        """API: 删除用户"""
        user = User.query.filter_by(id=user_id, tenant_id=current_tenant_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # 记录审计日志
        log_audit('delete_user', user.id, {'user_id': user_id})
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'success': True})
    
    @expose('/api/audit-logs', methods=['GET'])
    def api_audit_logs(self):
        """API: 获取审计日志"""
        return jsonify(audit_logs[-100:])  # 返回最近100条日志

# 注册蓝图
@user_bp.record_once
def on_load(state):
    """蓝图加载完成后执行"""
    # 可以在这里初始化一些资源
    pass