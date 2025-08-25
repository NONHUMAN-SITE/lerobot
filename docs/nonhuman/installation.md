# Guía de instalación y ejecución

Para poder ejecutar este repositorio de forma correcta necesitas
instalar **Miniconda** primero.

------------------------------------------------------------------------

## 1. Instalar Miniconda

Abre tu terminal (puedes hacerlo con `Ctrl + Alt + T` o buscando
"Terminal" en tus aplicaciones) y ejecuta los siguientes comandos:

``` bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash ~/Miniconda3-latest-Linux-x86_64.sh
```

Durante la instalación acepta todas las opciones por defecto y responde
`yes` cuando se te pregunte.

------------------------------------------------------------------------

## 2. Crear un nuevo environment con Conda

Una vez instalada Miniconda, crea un environment llamado `biman` con
**Python 3.13**:

``` bash
conda create --name biman python=3.13
```

Cuando se haya creado, actívalo con:

``` bash
conda activate biman
```

------------------------------------------------------------------------

## 3. Clonar el repositorio

Clona este repositorio desde GitHub:

``` bash
git clone https://github.com/NONHUMAN-SITE/lerobot
```

Accede a la carpeta clonada:

``` bash
cd lerobot
```

Asegúrate de que tu environment está activo; tu terminal debería verse
algo así:

``` bash
(biman) [usuario]@[nombre-pc]:~/NONHUMAN/lerobot$
```

------------------------------------------------------------------------

## 4. Instalar dependencias

Dentro de la carpeta raíz del repositorio, instala las dependencias con:

``` bash
pip install -e .
```

Espera a que finalice la instalación.

------------------------------------------------------------------------

✅ ¡Listo! Ahora tu entorno está configurado correctamente para ejecutar
el repositorio.