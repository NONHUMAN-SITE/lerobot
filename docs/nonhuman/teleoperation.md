Perfecto 🙌 aquí te dejo el **README.md** en markdown, paso a paso y bien estructurado:

---

````markdown
# Guía de Teleoperación del Sistema

Este documento explica cómo configurar y utilizar el sistema de teleoperación.  
Asegúrate de que todo el hardware esté conectado de forma óptima antes de comenzar.

---

## 1. Preparar las cámaras y puertos USB

1. Utiliza una **extensión de conector a USB** para ampliar la cantidad de puertos disponibles.  
   (Si no la tienes, pide a alguien del grupo que te la proporcione).
2. Conecta los **brazos robóticos** en el siguiente orden dentro de los puertos USB:
   - Follower izquierdo  
   - Follower derecho  
   - Leader izquierdo  
   - Leader derecho  
3. Una vez conectados los brazos, procede a conectar las **cámaras**.
4. Asegúrate de que la **fuente de poder de los robots** esté encendida.

---

## 2. Configurar los archivos de calibración

Copia los archivos de calibración en la ruta de HuggingFace cache:

```bash
dest="/home/[usuario]/.cache/huggingface" && mkdir -p "$dest" && cp -r calibration "$dest"
````

⚠️ **Importante:** reemplaza `[usuario]` con tu nombre de usuario en el sistema.

---

## 3. Configurar los puertos de los robots

1. Con todo conectado, ejecuta:

```bash
ls /dev/ttyACM*
```

Si todo está bien, deberías ver algo como:

```
/dev/ttyACM0 /dev/ttyACM1 /dev/ttyACM2 /dev/ttyACM3
```

2. Para identificar cada puerto:

   * Desconecta uno de los brazos.
   * Ejecuta nuevamente el comando `ls /dev/ttyACM*`.
   * El puerto que desaparezca corresponde a ese brazo.

3. Registra el puerto en el archivo correspondiente:

   * `teleoperation.sh`
   * `record_bimanual.sh`

---

## 4. Configurar las cámaras

Ejecuta el test de cámaras:

```bash
python tests/camera_test.py
```

Esto generará una carpeta llamada `captured_images/` donde cada imagen tendrá un **ID**.
Ese ID corresponde al **puerto de la cámara** respectiva.

---

## 5. Probar la teleoperación

Cuando hayas configurado todos los puertos de los brazos y cámaras, ejecuta:

```bash
bash teleoperation.sh
```

Ahora ya deberías poder teleoperar el sistema.

---

## 6. Recolectar datos

Para comenzar la recolección de datos, ejecuta:

```bash
bash record_bimanual.sh
```

Esto abrirá una **interfaz de control** en la que podrás manejar el flujo de los episodios:

* ⬅️ **Flecha izquierda** → Reinicia el episodio
* ➡️ **Flecha derecha** → Termina el episodio

⚠️ **Importante:** Si un episodio sale mal, reinícialo con la flecha izquierda.
Cuando quieras terminarlo, usa la flecha derecha **solo una vez** (evita presionar dos veces).

---

✅ ¡Listo! Con esto ya puedes teleoperar y recolectar datos correctamente.

```

---

¿Quieres que te prepare también un **diagrama visual en markdown con puertos y dispositivos conectados** (tipo ASCII/tabla) para que quede más claro el orden de conexión?
```
