"""Inicia MentorIA:  python app.py   →  http://127.0.0.1:8000

Opciones:
  python app.py --puerto 8080
  python app.py --red          (permite abrirlo desde un celular en la misma red Wi-Fi)
"""
import argparse
import socket
import webbrowser

from mentoria.server import VERSION, iniciar


def main():
    p = argparse.ArgumentParser(description="MentorIA – MVP")
    p.add_argument("--puerto", type=int, default=8000)
    p.add_argument("--red", action="store_true", help="escuchar en la red local (acceso desde el celular)")
    p.add_argument("--sin-navegador", action="store_true")
    a = p.parse_args()
    host = "0.0.0.0" if a.red else "127.0.0.1"
    servidor, app = iniciar(host, a.puerto)
    url = f"http://127.0.0.1:{a.puerto}"
    print(f"MentorIA {VERSION} – {len(app.indice.fragmentos)} fragmentos de sílabo indexados")
    print(f"Abrir en el navegador: {url}")
    if a.red:
        print(f"Desde el celular: http://{socket.gethostbyname(socket.gethostname())}:{a.puerto}")
    print("Ctrl+C para detener.")
    if not a.sin_navegador:
        webbrowser.open(url)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")


if __name__ == "__main__":
    main()
