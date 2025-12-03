
from flask import Flask, jsonify, request
from flask_cors import CORS
import os, json, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
CORS(app)  # permite llamadas desde Netlify

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EMPRESAS_DIR = os.path.join(BASE_DIR, "empresas")

def cargar_json(ruta):
    if os.path.exists(ruta):
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

@app.route("/empresa/<empresa_id>/config", methods=["GET"])
def get_config(empresa_id):
    ruta = os.path.join(EMPRESAS_DIR, empresa_id, "config.json")
    data = cargar_json(ruta)
    if not data:
        return jsonify({"error": "Empresa no encontrada"}), 404
    return jsonify(data)

@app.route("/empresa/<empresa_id>/faq", methods=["GET"])
def get_faq(empresa_id):
    ruta = os.path.join(EMPRESAS_DIR, empresa_id, "faq.json")
    data = cargar_json(ruta)
    if not data:
        return jsonify({"error": "FAQ no encontrado"}), 404
    return jsonify(data)

@app.route("/empresa/<empresa_id>/promos", methods=["GET"])
def get_promos(empresa_id):
    ruta = os.path.join(EMPRESAS_DIR, empresa_id, "promos.json")
    data = cargar_json(ruta)
    if not data:
        return jsonify({"error": "Promos no encontrado"}), 404
    return jsonify(data)

# Genera link de pago simple: linkPagoBase + monto
@app.route("/pago/<empresa_id>/qr", methods=["POST"])
def generar_link_qr(empresa_id):
    payload = request.json or {}
    monto = str(payload.get("monto", "")).strip()
    cfg = cargar_json(os.path.join(EMPRESAS_DIR, empresa_id, "config.json"))
    if not cfg:
        return jsonify({"error": "Empresa no encontrada"}), 404
    base = cfg.get("linkPagoBase", "")
    if not base or not monto:
        return jsonify({"error": "Faltan datos para generar pago"}), 400
    link = f"{base}{monto}"
    return jsonify({"linkPago": link})

# Envía correo al dueño con los datos del pedido
@app.route("/notify/<empresa_id>", methods=["POST"])
def notify_owner(empresa_id):
    datos = request.json or {}
    cfg = cargar_json(os.path.join(EMPRESAS_DIR, empresa_id, "config.json"))
    if not cfg:
        return jsonify({"error": "Empresa no encontrada"}), 404

    correo_destino = cfg.get("correo")
    if not correo_destino:
        return jsonify({"error": "Correo de destino no configurado"}), 400

    # Variables de entorno (configúralas en Render)
    email_user = os.getenv("EMAIL_USER")
    email_pass = os.getenv("EMAIL_PASS")

    if not email_user or not email_pass:
        return jsonify({"error": "EMAIL_USER/EMAIL_PASS no configurados"}), 500

    asunto = f"Nuevo pedido - {cfg.get('nombre', empresa_id)}"
    cuerpo = (
        f"Nuevo pedido:\n\n"
        f"Nombre: {datos.get('nombre','')}\n"
        f"Teléfono: {datos.get('telefono','')}\n"
        f"Detalle: {datos.get('detalle','')}\n"
        f"Monto: {datos.get('monto','')}\n"
    )

    try:
        msg = MIMEMultipart()
        msg["From"] = email_user
        msg["To"] = correo_destino
        msg["Subject"] = asunto
        msg.attach(MIMEText(cuerpo, "plain"))

        smtp = smtplib.SMTP("smtp.gmail.com", 587)
        smtp.starttls()
        smtp.login(email_user, email_pass)
        smtp.sendmail(email_user, correo_destino, msg.as_string())
        smtp.quit()

        return jsonify({"status": "Notificación enviada ✅"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def root():
    return jsonify({"status": "Backend OK"})

if __name__ == "__main__":
    # Para pruebas locales
    app.run(host="127.0.0.1", port=5000, debug=True)
