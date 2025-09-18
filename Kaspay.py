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
    page_title="多币种支付系统",
    page_icon="💰",
    layout="wide"
)

# 初始化session state
if 'payment_orders' not in st.session_state:
    st.session_state.payment_orders = {}
if 'crypto_prices' not in st.session_state:
    st.session_state.crypto_prices = {
        'kaspa': 0.15,
        'dogecoin': 0.08,
        'litecoin': 75.0
    }
if 'auto_refresh_enabled' not in st.session_state:
    st.session_state.auto_refresh_enabled = False

class MultiCryptoPaymentSystem:
    def __init__(self):
        # 各币种网络配置
        self.crypto_configs = {
            'kaspa': {
                'name': 'Kaspa',
                'symbol': 'KAS',
                'icon': '💎',
                'api_base': "https://api.kaspa.org",
                'merchant_address': "kaspa:qz8z7g3q4x5w6v7u8t9s0r1q2p3o4n5m6l7k8j9h0g1f2e3d4c5b6a7",
                'uri_prefix': 'kaspa:',
                'coingecko_id': 'kaspa',
                'decimals': 8
            },
            'dogecoin': {
                'name': 'Dogecoin',
                'symbol': 'DOGE',
                'icon': '🐕',
                'api_base': "https://dogechain.info/api/v1",
                'merchant_address': "DH5yaieqoZN36fDVciNyRueRGvGLR3mr7L",
                'uri_prefix': 'dogecoin:',
                'coingecko_id': 'dogecoin',
                'decimals': 8
            },
            'litecoin': {
                'name': 'Litecoin',
                'symbol': 'LTC',
                'icon': '🔶',
                'api_base': "https://api.blockcypher.com/v1/ltc/main",
                'merchant_address': "LdP8Qox1VAhCzLJNqrr74YovaWYyNBUWvL",
                'uri_prefix': 'litecoin:',
                'coingecko_id': 'litecoin',
                'decimals': 8
            }
        }
        
    def get_crypto_prices(self):
        """获取所有支持币种的当前价格（USD）"""
        try:
            # 获取所有币种的价格
            coin_ids = ','.join([config['coingecko_id'] for config in self.crypto_configs.values()])
            response = requests.get(
                f"https://api.coingecko.com/api/v3/simple/price?ids={coin_ids}&vs_currencies=usd",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                prices = {}
                for crypto, config in self.crypto_configs.items():
                    coin_id = config['coingecko_id']
                    if coin_id in data:
                        prices[crypto] = data[coin_id]['usd']
                    else:
                        prices[crypto] = st.session_state.crypto_prices[crypto]
                return prices
            else:
                return st.session_state.crypto_prices
        except Exception as e:
            st.error(f"获取价格失败: {e}")
            return st.session_state.crypto_prices
    
    def create_payment_order(self, amount_usd, crypto_type, description=""):
        """创建支付订单"""
        order_id = str(uuid.uuid4())
        prices = self.get_crypto_prices()
        crypto_price = prices[crypto_type]
        crypto_amount = round(amount_usd / crypto_price, self.crypto_configs[crypto_type]['decimals'])
        
        order = {
            'id': order_id,
            'amount_usd': amount_usd,
            'crypto_type': crypto_type,
            'crypto_amount': crypto_amount,
            'crypto_price': crypto_price,
            'crypto_symbol': self.crypto_configs[crypto_type]['symbol'],
            'crypto_name': self.crypto_configs[crypto_type]['name'],
            'description': description,
            'status': 'pending',
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(minutes=30),
            'payment_address': self.crypto_configs[crypto_type]['merchant_address'],
            'txid': None
        }
        
        return order
    
    def generate_qr_code(self, crypto_type, address, amount, message=""):
        """生成加密货币支付二维码"""
        if not QR_AVAILABLE:
            return None
            
        # 构建支付URI
        config = self.crypto_configs[crypto_type]
        crypto_uri = f"{config['uri_prefix']}{address}?amount={amount}"
        if message:
            crypto_uri += f"&message={message}"
            
        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(crypto_uri)
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
    
    def get_crypto_uri(self, crypto_type, address, amount, message=""):
        """获取加密货币支付URI"""
        config = self.crypto_configs[crypto_type]
        crypto_uri = f"{config['uri_prefix']}{address}?amount={amount}"
        if message:
            crypto_uri += f"&message={message}"
        return crypto_uri
    
    def check_payment_status(self, order_id, expected_amount, address, crypto_type):
        """检查支付状态"""
        try:
            # 这里应该调用对应币种的区块链API检查地址余额变化
            # 不同币种需要不同的API调用方式
            
            config = self.crypto_configs[crypto_type]
            
            if crypto_type == 'kaspa':
                # Kaspa API调用逻辑
                pass
            elif crypto_type == 'dogecoin':
                # Dogecoin API调用逻辑 (DogeChain API)
                # response = requests.get(f"{config['api_base']}/address/balance/{address}")
                pass
            elif crypto_type == 'litecoin':
                # Litecoin API调用逻辑 (BlockCypher API)
                # response = requests.get(f"{config['api_base']}/addrs/{address}/balance")
                pass
            
            # 为演示目的返回模拟状态
            return 'pending'
            
        except Exception as e:
            st.error(f"检查支付状态失败: {e}")
            return 'error'

# 创建支付系统实例
payment_system = MultiCryptoPaymentSystem()

# 主界面
st.title("💰 多币种支付系统")
st.markdown("支持 Kaspa 💎 | Dogecoin 🐕 | Litecoin 🔶")
st.markdown("---")

# 侧边栏
with st.sidebar:
    st.header("实时币价")
    crypto_prices = payment_system.get_crypto_prices()
    st.session_state.crypto_prices = crypto_prices
    
    for crypto, config in payment_system.crypto_configs.items():
        price = crypto_prices[crypto]
        st.metric(
            f"{config['icon']} {config['name']}", 
            f"${price:.4f}" if price < 1 else f"${price:.2f}", 
            delta=None
        )
    
    st.header("商户信息")
    selected_crypto = st.selectbox(
        "查看收款地址:",
        options=list(payment_system.crypto_configs.keys()),
        format_func=lambda x: f"{payment_system.crypto_configs[x]['icon']} {payment_system.crypto_configs[x]['name']}"
    )
    
    if selected_crypto:
        address = payment_system.crypto_configs[selected_crypto]['merchant_address']
        st.text(f"{selected_crypto.upper()}收款地址:")
        st.code(address[:25] + "...")
    
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
        
        # 选择加密货币
        crypto_type = st.selectbox(
            "选择支付币种",
            options=list(payment_system.crypto_configs.keys()),
            format_func=lambda x: f"{payment_system.crypto_configs[x]['icon']} {payment_system.crypto_configs[x]['name']} ({payment_system.crypto_configs[x]['symbol']})",
            index=0
        )
        
        description = st.text_input(
            "支付描述", 
            placeholder="输入支付描述..."
        )
        
        if st.button("创建支付订单", type="primary"):
            order = payment_system.create_payment_order(amount_usd, crypto_type, description)
            st.session_state.payment_orders[order['id']] = order
            st.success(f"支付订单已创建! 订单ID: {order['id'][:8]}...")
            st.info("订单已创建，请切换到 '📊 订单管理' 选项卡查看详情")
    
    with col2:
        st.subheader("实时汇率预览")
        if crypto_type:
            config = payment_system.crypto_configs[crypto_type]
            price = crypto_prices[crypto_type]
            crypto_amount = round(amount_usd / price, config['decimals'])
            
            st.metric(
                f"需要支付 {config['symbol']}", 
                f"{crypto_amount} {config['symbol']}",
                delta=f"${price:.4f} /{config['symbol']}"
            )
            
            # 显示其他币种的等值金额
            st.write("**其他币种等值:**")
            for other_crypto, other_config in payment_system.crypto_configs.items():
                if other_crypto != crypto_type:
                    other_price = crypto_prices[other_crypto]
                    other_amount = round(amount_usd / other_price, other_config['decimals'])
                    st.write(f"{other_config['icon']} {other_amount} {other_config['symbol']}")

with tab2:
    st.header("支付订单管理")
    
    # 添加批量操作按钮
    col1, col2, col3, col4 = st.columns(4)
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
    
    with col3:
        # 按币种筛选
        filter_crypto = st.selectbox(
            "筛选币种",
            options=['all'] + list(payment_system.crypto_configs.keys()),
            format_func=lambda x: '全部' if x == 'all' else f"{payment_system.crypto_configs[x]['icon']} {payment_system.crypto_configs[x]['name']}",
            index=0
        )
    
    # 显示订单统计
    if st.session_state.payment_orders:
        total_orders = len(st.session_state.payment_orders)
        pending_orders = sum(1 for order in st.session_state.payment_orders.values() if order['status'] == 'pending')
        confirmed_orders = sum(1 for order in st.session_state.payment_orders.values() if order['status'] == 'confirmed')
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("总订单", total_orders)
        with col2:
            st.metric("待支付", pending_orders)
        with col3:
            st.metric("已完成", confirmed_orders)
        with col4:
            expired_orders = sum(1 for order in st.session_state.payment_orders.values() if order['status'] == 'expired')
            st.metric("已过期", expired_orders)
    
    # 显示订单列表
    if st.session_state.payment_orders:
        # 筛选订单
        filtered_orders = {}
        for order_id, order in st.session_state.payment_orders.items():
            if filter_crypto == 'all' or order['crypto_type'] == filter_crypto:
                filtered_orders[order_id] = order
        
        if not filtered_orders:
            st.info(f"没有找到 {payment_system.crypto_configs.get(filter_crypto, {}).get('name', '所选')} 的订单")
        else:
            for order_id, order in filtered_orders.items():
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
                
                # 获取币种配置
                crypto_config = payment_system.crypto_configs[order['crypto_type']]
                
                with st.expander(f"{status_icon} {crypto_config['icon']} 订单 {order_id[:8]} - {order['status'].upper()}", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write("**订单信息**")
                        st.write(f"金额: ${order['amount_usd']:.2f}")
                        st.write(f"{crypto_config['name']}: {order['crypto_amount']:.{crypto_config['decimals']}f} {crypto_config['symbol']}")
                        st.write(f"状态: {order['status']}")
                        st.write(f"描述: {order.get('description', '无')}")
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
                        st.write(f"**{crypto_config['name']} 支付地址**")
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
                        
                        # 显示支付URI
                        crypto_uri = payment_system.get_crypto_uri(
                            order['crypto_type'],
                            order['payment_address'],
                            order['crypto_amount'],
                            order['description']
                        )
                        st.code(crypto_uri, language=None)
                        
                        # 显示二维码（如果可用）
                        if QR_AVAILABLE:
                            qr_code = payment_system.generate_qr_code(
                                order['crypto_type'],
                                order['payment_address'],
                                order['crypto_amount'],
                                order['description']
                            )
                            if qr_code:
                                st.image(f"data:image/png;base64,{qr_code}", width=200)
                        else:
                            st.info("安装 qrcode[pil] 库以显示二维码")
                            # 提供URI复制框
                            st.text_input(
                                "复制支付URI:",
                                value=crypto_uri,
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
                                    order['crypto_amount'], 
                                    order['payment_address'],
                                    order['crypto_type']
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
        
        # 为每种币种配置API端点和地址
        for crypto, config in payment_system.crypto_configs.items():
            st.write(f"**{config['icon']} {config['name']} 设置**")
            
            api_endpoint = st.text_input(
                f"{config['name']} API端点", 
                value=config['api_base'],
                key=f"api_{crypto}"
            )
            
            merchant_address = st.text_area(
                f"{config['name']} 商户收款地址",
                value=config['merchant_address'],
                height=60,
                key=f"address_{crypto}"
            )
            
            st.markdown("---")
    
    with col2:
        st.subheader("支付设置")
        
        default_expiry = st.number_input(
            "默认订单过期时间(分钟)", 
            min_value=5, 
            max_value=1440, 
            value=30
        )
        
        confirmation_blocks = st.number_input(
            "所需确认区块数", 
            min_value=1, 
            max_value=100, 
            value=6
        )
        
        st.subheader("显示设置")
        
        show_usd_equivalent = st.checkbox("显示USD等值", value=True)
        show_other_crypto_equivalent = st.checkbox("显示其他币种等值", value=True)
        
        st.info("💡 **提示**: 使用侧边栏的 '🔄 刷新页面' 按钮或订单管理中的检查按钮来更新状态")
    
    if st.button("保存设置"):
        st.success("设置已保存!")

# 页面底部信息
st.markdown("---")
st.markdown(f"""
<div style='text-align: center'>
    <p>多币种支付系统 v2.0 | 基于Streamlit构建</p>
    <p>支持的币种: {' | '.join([f"{config['icon']} {config['name']}" for config in payment_system.crypto_configs.values()])}</p>
    <p>⚠️ 注意：这是一个演示系统，请勿用于生产环境</p>
    <p>💡 使用侧边栏的刷新按钮来更新页面状态</p>
</div>
""", unsafe_allow_html=True)