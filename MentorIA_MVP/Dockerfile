# Imagen para publicar MentorIA (Render, Hugging Face Spaces u otro servicio con Docker).
# Solo usa la biblioteca estándar de Python: no hay requirements que instalar.
FROM python:3.12-slim

# Se ejecuta con un usuario sin privilegios (uid 1000); los datos deben poder escribirse.
RUN useradd -m -u 1000 user
USER user
ENV PYTHONUNBUFFERED=1 PYTHONIOENCODING=utf-8
# Hora de Perú (UTC−5, sin horario de verano) para las fechas de las consultas.
ENV TZ=<-05>5

WORKDIR /home/user/app
COPY --chown=user . .

EXPOSE 7860
# Cada vez que el servicio arranca se cargan los datos de demostración (datos simulados).
# Render indica el puerto en la variable PORT; sin ella se usa 7860.
CMD ["sh", "-c", "python seed_demo.py && python app.py --red --sin-navegador --puerto ${PORT:-7860}"]
