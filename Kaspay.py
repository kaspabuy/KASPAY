import streamlit as st
import requests
import json
import time
import hashlib
import uuid
from datetime import datetime, timedelta
from io import BytesIO
import base64

# 尝试导入qrcode，如果失败则提供替代方案
try:
    import qrcode
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False
    st.warning("⚠️ qrcode库未安装。请运行: pip install qrcode[pil] 来启用二维码功能")

# 尝试导入PIL，如果失败则提供提示
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# 页面配置
st.set_page_config(
    page_title="Kaspa支付系统",
    page_icon="💎",
    layout="wide"
)

# 初始化session state
if 'payment_orders' not in st.session_state:
    st.session_state.payment_orders = {}
if 'kaspa_price' not in st.session_state:
    st.session_state.kaspa_price = 0.15  # 默认价格，实际应该从API获取
if 'auto_refresh_enabled' not in st.session_state:
    st.session_state.auto_refresh_enabled = False

class KaspaPaymentSystem:
    def __init__(self):
        # Kaspa网络配置
        self.kaspa_api_base = "https://api.kaspa.org"  # 示例API地址
        self.merchant_address = "kaspa:qz8z7g3q4x5w6v7u8t9s0r1q2p3o4n5m6l7k8j9h0g1f2e3d4c5b6a7"
        
    def get_kaspa_price(self):
        """获取Kaspa当前价格（USD）"""
        try:
            # 这里应该连接真实的价格API
            # 示例：CoinGecko API
            response = requests.get(
                "https://api.coingecko.com/api/v3/simple/price?ids=kaspa&vs_currencies=usd",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return data['kaspa']['usd']
            else:
                return st.session_state.kaspa_price
        except Exception as e:
            st.error(f"获取价格失败: {e}")
            return st.session_state.kaspa_price
    
    def create_payment_order(self, amount_usd, description=""):
        """创建支付订单"""
        order_id = str(uuid.uuid4())
        kaspa_price = self.get_kaspa_price()
        kaspa_amount = round(amount_usd / kaspa_price, 8)
        
        order = {
            'id': order_id,
            'amount_usd': amount_usd,
            'kaspa_amount': kaspa_amount,
            'kaspa_price': kaspa_price,
            'description': description,
            'status': 'pending',
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(minutes=30),
            'payment_address': self.merchant_address,
            'txid': None
        }
        
        return order
    
    def generate_qr_code(self, address, amount, message=""):
        """生成Kaspa支付二维码"""
        if not QR_AVAILABLE:
            return None
            
        # Kaspa URI格式
        kaspa_uri = f"kaspa:{address}?amount={amount}"
        if message:
            kaspa_uri += f"&message={message}"
            
        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(kaspa_uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # 转换为base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return img_str
        except Exception as e:
            st.error(f"生成二维码失败: {e}")
            return None
    
    def get_kaspa_uri(self, address, amount, message=""):
        """获取Kaspa支付URI"""
        kaspa_uri = f"kaspa:{address}?amount={amount}"
        if message:
            kaspa_uri += f"&message={message}"
        return kaspa_uri
    
    def check_payment_status(self, order_id, expected_amount, address):
        """检查支付状态"""
        try:
            # 这里应该调用Kaspa区块链API检查地址余额变化
            # 示例代码，实际需要连接真实的Kaspa节点或API
            
            # 模拟API调用
            # response = requests.get(f"{self.kaspa_api_base}/address/{address}/transactions")
            
            # 为演示目的，这里返回模拟状态
            # 在实际应用中，您需要：
            # 1. 查询地址的最新交易
            # 2. 检查是否有匹配金额的入账
            # 3. 验证交易确认数
            
            return 'pending'  # 可能的状态：pending, confirmed, failed, expired
            
        except Exception as e:
            st.error(f"检查支付状态失败: {e}")
            return 'error'

# 创建支付系统实例
payment_system = KaspaPaymentSystem()

# 主界面
st.title("💎 Kaspa支付系统")
st.markdown("---")

# 侧边栏
with st.sidebar:
    st.header("系统状态")
    kaspa_price = payment_system.get_kaspa_price()
    st.session_state.kaspa_price = kaspa_price
    st.metric("Kaspa价格", f"${kaspa_price:.4f}", delta=None)
    
    st.header("商户信息")
    st.text(f"收款地址:")
    st.code(payment_system.merchant_address[:20] + "...")
    
    # 添加手动刷新按钮
    if st.button("🔄 刷新页面", type="secondary"):
        st.rerun()

# 主要功能选项卡
tab1, tab2, tab3 = st.tabs(["💳 创建支付", "📊 订单管理", "⚙️ 设置"])

with tab1:
    st.header("创建新的支付订单")
    
    col1, col2 = st.columns(2)
    
    with col1:
        amount_usd = st.number_input(
            "支付金额 (USD)", 
            min_value=0.01, 
            max_value=10000.0, 
            value=10.0,
            step=0.01
        )
        
        description = st.text_input(
            "支付描述", 
            placeholder="输入支付描述..."
        )
        
        if st.button("创建支付订单", type="primary"):
            order = payment_system.create_payment_order(amount_usd, description)
            st.session_state.payment_orders[order['id']] = order
            st.success(f"支付订单已创建! 订单ID: {order['id'][:8]}...")
            # 切换到订单管理页面
            st.info("订单已创建，请切换到 '📊 订单管理' 选项卡查看详情")
    
    with col2:
        st.subheader("实时汇率")
        st.metric(
            "当前汇率", 
            f"1 USD = {1/kaspa_price:.2f} KAS",
            delta=f"{kaspa_price:.4f} USD/KAS"
        )

with tab2:
    st.header("支付订单管理")
    
    # 添加批量操作按钮
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 检查所有订单状态"):
            for order_id in st.session_state.payment_orders:
                order = st.session_state.payment_orders[order_id]
                if order['status'] == 'pending':
                    # 检查是否过期
                    if datetime.now() > order['expires_at']:
                        st.session_state.payment_orders[order_id]['status'] = 'expired'
            st.rerun()
    
    with col2:
        if st.button("🗑️ 清除已过期订单"):
            expired_orders = [
                order_id for order_id, order in st.session_state.payment_orders.items()
                if order['status'] == 'expired'
            ]
            for order_id in expired_orders:
                del st.session_state.payment_orders[order_id]
            if expired_orders:
                st.success(f"已清除 {len(expired_orders)} 个过期订单")
                st.rerun()
            else:
                st.info("没有过期订单需要清除")
    
    if st.session_state.payment_orders:
        for order_id, order in st.session_state.payment_orders.items():
            # 自动检查过期状态
            if order['status'] == 'pending' and datetime.now() > order['expires_at']:
                st.session_state.payment_orders[order_id]['status'] = 'expired'
                order['status'] = 'expired'
            
            # 根据状态设置展开器的图标
            status_icon = {
                'pending': '⏳',
                'confirmed': '✅',
                'expired': '❌',
                'failed': '❌'
            }.get(order['status'], '❓')
            
            with st.expander(f"{status_icon} 订单 {order_id[:8]} - {order['status'].upper()}", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write("**订单信息**")
                    st.write(f"金额: ${order['amount_usd']:.2f}")
                    st.write(f"Kaspa: {order['kaspa_amount']:.8f} KAS")
                    st.write(f"状态: {order['status']}")
                    st.write(f"创建时间: {order['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
                    st.write(f"过期时间: {order['expires_at'].strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    # 显示倒计时
                    if order['status'] == 'pending':
                        time_left = order['expires_at'] - datetime.now()
                        if time_left.total_seconds() > 0:
                            minutes_left = int(time_left.total_seconds() / 60)
                            st.write(f"⏰ 剩余时间: {minutes_left} 分钟")
                        else:
                            st.write("⏰ 已过期")
                
                with col2:
                    st.write("**支付地址**")
                    st.code(order['payment_address'])
                    
                    # 使用文本框让用户手动复制
                    st.text_input(
                        "复制地址:",
                        value=order['payment_address'],
                        key=f"addr_copy_{order_id}",
                        label_visibility="collapsed"
                    )
                
                with col3:
                    st.write("**支付信息**")
                    
                    # 显示Kaspa URI
                    kaspa_uri = payment_system.get_kaspa_uri(
                        order['payment_address'],
                        order['kaspa_amount'],
                        order['description']
                    )
                    st.code(kaspa_uri, language=None)
                    
                    # 显示二维码（如果可用）
                    if QR_AVAILABLE:
                        qr_code = payment_system.generate_qr_code(
                            order['payment_address'],
                            order['kaspa_amount'],
                            order['description']
                        )
                        if qr_code:
                            st.image(f"data:image/png;base64,{qr_code}", width=200)
                    else:
                        st.info("安装 qrcode[pil] 库以显示二维码")
                        # 提供URI复制框
                        st.text_input(
                            "复制支付URI:",
                            value=kaspa_uri,
                            key=f"uri_copy_{order_id}",
                            label_visibility="collapsed"
                        )
                
                # 支付状态检查
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"🔍 检查支付状态", key=f"check_{order_id}"):
                        with st.spinner("检查中..."):
                            status = payment_system.check_payment_status(
                                order_id, 
                                order['kaspa_amount'], 
                                order['payment_address']
                            )
                            st.session_state.payment_orders[order_id]['status'] = status
                            st.success(f"状态已更新: {status}")
                            st.rerun()
                
                with col2:
                    if order['status'] == 'pending':
                        if st.button(f"✅ 标记为已完成", key=f"confirm_{order_id}"):
                            st.session_state.payment_orders[order_id]['status'] = 'confirmed'
                            st.success("订单已标记为完成！")
                            st.rerun()
                
                with col3:
                    if st.button(f"🗑️ 删除订单", key=f"delete_{order_id}", type="secondary"):
                        del st.session_state.payment_orders[order_id]
                        st.success("订单已删除！")
                        st.rerun()
    else:
        st.info("暂无支付订单")
        st.markdown("💡 **提示**: 前往 '💳 创建支付' 选项卡创建新的支付订单")

with tab3:
    st.header("系统设置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("网络设置")
        
        api_endpoint = st.text_input(
            "Kaspa API端点", 
            value="https://api.kaspa.org"
        )
        
        merchant_address = st.text_area(
            "商户收款地址",
            value=payment_system.merchant_address,
            height=100
        )
        
        confirmation_blocks = st.number_input(
            "所需确认区块数", 
            min_value=1, 
            max_value=100, 
            value=6
        )
    
    with col2:
        st.subheader("支付设置")
        
        default_expiry = st.number_input(
            "默认订单过期时间(分钟)", 
            min_value=5, 
            max_value=1440, 
            value=30
        )
        
        # 移除自动刷新选项，避免性能问题
        st.info("💡 **提示**: 使用侧边栏的 '🔄 刷新页面' 按钮或订单管理中的检查按钮来更新状态")
    
    if st.button("保存设置"):
        # 这里可以保存设置到session state或配置文件
        st.success("设置已保存!")

# 页面底部信息
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>Kaspa支付系统 v1.0 | 基于Streamlit构建</p>
    <p>⚠️ 注意：这是一个演示系统，请勿用于生产环境</p>
    <p>💡 使用侧边栏的刷新按钮来更新页面状态</p>
</div>
""", unsafe_allow_html=True)