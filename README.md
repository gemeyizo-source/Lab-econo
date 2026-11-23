# Laboratorio web de internacionalización empresarial

Aplicación académica interactiva basada en cálculo diferencial e integral. Adaptada de Tkinter a Streamlit para uso en navegador.

## Características

- Modelos de ingreso marginal, demanda internacional, conversión de ventas, costos marginales, costos financieros y fondo de inversión.
- Escenarios base, optimista y pesimista; parámetros configurables en el navegador.
- Seis gráficas interactivas, KPIs, interpretación y tabla mensual.
- Descargas CSV y PDF; simulación de 12 o 24 meses.

## Publicación con URL pública

1. Iniciar sesión en https://github.com y crear un repositorio nuevo, **Public**, por ejemplo `laboratorio-internacionalizacion`.
2. Abrir el repositorio, ir a **Add file > Upload files** (o *uploading an existing file* si está vacío).
3. **Descomprimir** el ZIP del proyecto y subir los archivos `app.py`, `requirements.txt` y `README.md`. Además, crear en GitHub el archivo `.streamlit/config.toml` con **Add file > Create new file** si no fue posible subir la carpeta con el navegador. Confirmar mediante **Commit changes**.
4. Ir a https://share.streamlit.io, iniciar sesión con GitHub y seleccionar **Create app** > **Yup, I have an app**.
5. Seleccionar el repositorio, la rama `main` y el archivo principal `app.py`.
6. Opcionalmente, elegir un nombre corto para el subdominio de la app; después presionar **Deploy**.
7. En **App settings > Sharing**, seleccionar **This app is public and searchable** (el repositorio público normalmente hace pública la app por defecto).
8. Compartir la URL HTTPS real que termina en `.streamlit.app`, que se asigna tras desplegar.

Los visitantes no necesitan una cuenta de GitHub ni instalar Python. La publicación requiere una cuenta del administrador de la app.

## Ejecutar localmente

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

En local, la dirección es `http://localhost:8501`; **no** es una dirección pública.

## Advertencia científica

Los resultados son ilustrativos y no equivalen a una evaluación de viabilidad real. El simulador asume `q(0)=0` y costo incremental `C(0)=0`. La conversión de demanda en ventas, los costos iniciales y la compatibilidad de unidades financieras requieren calibración. Se utiliza coseno en el costo financiero, de acuerdo con la formulación de la metodología original; el artículo presenta otra formulación en la discusión.

Referencia: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
