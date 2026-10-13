import streamlit as st
import time
import requests
import hmac
import hashlib
import json
import os
from urllib.parse import urlencode

CONFIG_FILE = "config.json"

st.set_page_config(page_title="LeoBot Panel", page_icon="🤖", layout="centered")

def cargar_configuracion():
    if not os.path.exists(CONFIG_FILE):
        return {
            "api_key": "",
            "secret_key": "",
            "bot_config": {
                "adv_no": "",
                "trade_type": "SELL",
                "asset": "USDT",
                "fiat": "VES",
                "monto_min_competidor": 4000.0,
                "precio_maximo_limite": 1005.00,
                "precio_minimo_limite": 999.00,
                "centavos_ajuste": 0.05,
                "intervalo_segundos": 6
            }
        }
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def guardar_configuracion(nueva_config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(nueva_config, f, indent=4)

def firmar_query_string(query_string, secret):
    return hmac.new(secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

def obtener_libro_p2p_publico(fiat, asset, trade_type, trans_amount):
    url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    search_type = "SELL" if trade_type == "BUY" else "BUY"
    payload = {
        "fiat": fiat, "page": 1, "rows": 10, "tradeType": search_type,
        "asset": asset, "countries": [], "proMerchantAds": False,
        "shieldMerchantAds": False, "publisherType": "merchant",
        "transAmount": trans_amount, "payTypes": ["BankTransfer", "BancoDeVenezuela"]
    }
    try:
        res = requests.post(url, json=payload, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data.get("code") == "000000":
                return data.get("data", [])
    except:
        pass
    return []

def actualizar_precio_comerciante(api_key, secret_key, adv_no, nuevo_precio, asset="USDT", fiat="VES"):
    url = "https://api.binance.com/sapi/v1/c2c/ads/update"
    headers = {
        'X-MBX-APIKEY': api_key.strip(),
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    server_time = int(time.time() * 1000)
    precio_str = f"{float(nuevo_precio):.2f}"
    
    # Parámetros estándar Binance C2C SAPI
    params = {
        "advNo": str(adv_no).strip(),
        "price": precio_str,
        "priceType": "1",
        "asset": str(asset).strip(),
        "fiat": str(fiat).strip(),
        "recvWindow": "60000",
        "timestamp": str(server_time)
    }
    
    # Ordenar alfabéticamente para la firma HMAC
    sorted_params = sorted(params.items())
    query_string = urlencode(sorted_params)
    signature = firmar_query_string(query_string, secret_key.strip())
    body_payload = f"{query_string}&signature={signature}"
    
    try:
        res = requests.post(url, headers=headers, data=body_payload, timeout=5)
        data = res.json()
        if res.status_code == 200 and (data.get("code") == "000000" or data.get("success") is True):
            return True, "Actualizado con éxito"
        else:
            msg_err = data.get('message') or data.get('msg') or str(data)
            return False, f"Code {data.get('code')}: {msg_err}"
    except Exception as e:
        return False, str(e)

# --- INTERFAZ GRÁFICA ---
st.title("🤖 LeoBot - Panel de Control P2P")
st.caption("Servidor en Nube de Repricing Automático")

cfg = cargar_configuracion()
bot_cfg = cfg.get("bot_config", {})

st.subheader("🔑 Credenciales API de Binance")
col1, col2 = st.columns(2)
with col1:
    api_key_input = st.text_input("API Key", value=cfg.get("api_key", ""), type="password")
with col2:
    secret_key_input = st.text_input("Secret Key", value=cfg.get("secret_key", ""), type="password")

st.divider()
st.subheader("📢 Anuncio Seleccionado")
adv_no_input = st.text_input("Número de Anuncio (advNo)", value=bot_cfg.get("adv_no", ""))
trade_type_input = st.selectbox("Tipo de Operación de tu Anuncio", ["SELL", "BUY"], index=0 if bot_cfg.get("trade_type", "SELL") == "SELL" else 1)

st.divider()
st.subheader("⚙️ Parámetros de Estrategia y Límites")

col3, col4, col5 = st.columns(3)
with col3:
    monto_min = st.number_input("Filtro Mínimo Competidor", value=float(bot_cfg.get("monto_min_competidor", 4000.0)))
with col4:
    ajuste = st.number_input("Centavos de Ajuste", value=float(bot_cfg.get("centavos_ajuste", 0.05)), format="%.2f")
with col5:
    intervalo = st.number_input("Intervalo (segundos)", value=int(bot_cfg.get("intervalo_segundos", 6)))

col_lim1, col_lim2 = st.columns(2)
with col_lim1:
    precio_max_input = st.number_input("🛡️ Precio Máximo (Tope Superior VES)", value=float(bot_cfg.get("precio_maximo_limite", 1005.00)), format="%.2f")
with col_lim2:
    precio_min_input = st.number_input("🛡️ Precio Mínimo (Piso Inferior VES)", value=float(bot_cfg.get("precio_minimo_limite", 999.00)), format="%.2f")

if st.button("💾 Guardar Configuración", type="primary"):
    nueva_data = {
        "api_key": api_key_input.strip(),
        "secret_key": secret_key_input.strip(),
        "bot_config": {
            "adv_no": adv_no_input.strip(),
            "trade_type": trade_type_input,
            "asset": "USDT",
            "fiat": "VES",
            "monto_min_competidor": monto_min,
            "precio_maximo_limite": precio_max_input,
            "precio_minimo_limite": precio_min_input,
            "centavos_ajuste": ajuste,
            "intervalo_segundos": intervalo
        }
    }
    guardar_configuracion(nueva_data)
    st.success("¡Configuración guardada correctamente en el servidor!")

st.divider()
st.subheader("🎮 Control de Ejecución")

if 'bot_ejecutando' not in st.session_state:
    st.session_state.bot_ejecutando = False

col_b1, col_b2 = st.columns(2)
with col_b1:
    if st.button("🚀 INICIAR BOT EN VIVO"):
        st.session_state.bot_ejecutando = True

with col_b2:
    if st.button("🛑 DETENER BOT"):
        st.session_state.bot_ejecutando = False
        st.warning("Bot pausado.")

if st.session_state.bot_ejecutando:
    st.info("🟢 Bot activo ejecutando repricing automático desde el servidor...")
    anuncios = obtener_libro_p2p_publico("VES", "USDT", trade_type_input, monto_min)
    if anuncios:
        p_comp = float(anuncios[0].get("adv", {}).get("price", 0))
        nuevo_p = round(p_comp - ajuste, 2) if trade_type_input == "SELL" else round(p_comp + ajuste, 2)
        
        if nuevo_p > precio_max_input:
            nuevo_p = precio_max_input
        elif nuevo_p < precio_min_input:
            nuevo_p = precio_min_input

        st.write(f"🔄 Competidor 1ro: **{p_comp:.2f} VES** | Objetivo: **{nuevo_p:.2f} VES**")
        exito, msj = actualizar_precio_comerciante(api_key_input, secret_key_input, adv_no_input, nuevo_p, "USDT", "VES")
        if exito:
            st.success(f"⚡ ¡Anuncio {adv_no_input} actualizado automáticamente a {nuevo_p:.2f} VES!")
        else:
            st.error(f"❌ {msj}")
            
    time.sleep(intervalo)
    st.rerun()