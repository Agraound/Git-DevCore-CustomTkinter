# 🧠 AETHERYON Dev Core - Git Control Console

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![CustomTkinter](https://img.shields.io/badge/CustomTkinter-5.2.0-green.svg)
![GitPython](https://img.shields.io/badge/GitPython-3.1.0-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**Una consola visual avanzada para control total de Git con interfaz moderna y detección inteligente de divergencias**

[Características](#-características) • [Instalación](#-instalación) • [Uso](#-uso) • [Capturas](#-capturas-de-pantalla) • [Contribuir](#-contribuir)

</div>

---

## 📋 Descripción

AETHERYON Dev Core es una aplicación de escritorio con interfaz gráfica que transforma la gestión de repositorios Git en una experiencia visual, intuitiva y potente. Diseñada para desarrolladores que buscan productividad sin sacrificar control.

### ✨ ¿Por qué AETHERYON Dev Core?

- 🎯 **Visualización clara**: Todos los archivos con su estado Git en tiempo real
- 🔍 **Detección inteligente**: Identifica automáticamente divergencias entre ramas
- 🚀 **Operaciones rápidas**: Add, Commit, Push, Pull, Merge en pocos clicks
- 🌿 **Gestión de ramas**: Crea, cambia y fusiona ramas con análisis previo
- 📊 **Historial completo**: Visualiza commits con detalles y filtros por archivo
- 🏷️ **Gestión de tags**: Crea y administra versiones fácilmente
- 🌐 **Integración GitHub**: Crea repositorios directamente desde la interfaz
- 🎨 **Interfaz oscura moderna**: Diseño limpio con CustomTkinter

---

## 🚀 Características

### 🔧 Operaciones Básicas
- ✅ Inicializar repositorios Git con `.gitignore` automático
- ➕ **Git Add** con selección múltiple de archivos
- 💾 **Git Commit** con mensajes predefinidos y personalizables
- 📊 **Git Status** en tiempo real con estados visuales
- 📜 **Git Log** con historial completo

### 🌿 Gestión de Ramas
- 🧪 Crear ramas nuevas desde cualquier punto
- 🔀 Cambiar entre ramas con verificación de estado
- 🔀 **Merge inteligente** con detección de conflictos
- 🍒 **Cherry-pick** de commits específicos
- ⚠️ **Detección automática de divergencias** entre ramas
- 🔍 Comparación visual de contenido entre ramas

### 🌐 Operaciones Remotas
- ⬆️ **Push** con confirmación
- ⬇️ **Pull** con actualización automática
- 🔄 **Fetch** para sincronizar referencias
- 📥 **Clone** de repositorios remotos
- 🌐 Crear repositorios en GitHub vía CLI

### 🏷️ Gestión Avanzada
- 🏷️ Crear y eliminar **tags** (versiones)
- 📊 Ver historial de commits por archivo
- 🔄 **Reset** (soft/mixed/hard) a commits específicos
- 🔍 Analizar divergencias manualmente
- 💻 Integración directa con VS Code

### 🎯 Características Especiales

#### 📊 Detección de Divergencias
```
Al cambiar de rama, AETHERYON detecta automáticamente:
✓ Archivos con versiones diferentes
✓ Timestamps y hashes de cada versión
✓ Cuál rama está más actualizada
✓ Si el merge será fast-forward o requerirá commit
```

#### 🔍 Comparador Visual
```
Compara archivos lado a lado:
✓ Contenido completo de ambas versiones
✓ Información de commits y autores
✓ Identificación de rama más reciente
```

#### 🚫 Filtrado Inteligente
```
Ignora automáticamente carpetas comunes:
✓ node_modules/
✓ venv/, env/, .venv/
✓ __pycache__/
✓ dist/, build/
✓ .next/, .nuxt/
✓ Y más...
```

---

## 📦 Instalación

### Requisitos Previos

- **Python 3.8+**
- **Git** instalado y configurado
- **GitHub CLI** (opcional, para crear repos en GitHub)

### Instalación Rápida

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/aetheryon-dev-core.git
cd aetheryon-dev-core

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la aplicación
python AETHERYON-Dev_Core_Customtkinter-Git.py
```

### Dependencias

```txt
customtkinter==5.2.0
GitPython==3.1.40
```

### Instalación de GitHub CLI (Opcional)

**Windows:**
```bash
winget install --id GitHub.cli
```

**macOS:**
```bash
brew install gh
```

**Linux:**
```bash
sudo apt install gh
```

Luego autenticarse:
```bash
gh auth login
```

---

## 🎮 Uso

### 1️⃣ Abrir un Proyecto

1. Click en **📂 Seleccionar**
2. Navega hasta la carpeta de tu proyecto
3. Si no tiene Git, puedes inicializarlo con **🚀 Iniciar Git**

### 2️⃣ Trabajar con Archivos

```
📊 Todos los archivos se muestran con su estado:
🆕 Untracked  → Archivos nuevos sin trackear
📝 Modificado → Archivos con cambios
✅ Staged     → Archivos listos para commit
💾 Committed  → Archivos sin cambios
```

**Flujo de trabajo típico:**
1. Hacer cambios en tu editor
2. Click **🔁 Refrescar** para ver cambios
3. Seleccionar archivos modificados
4. **➕ Git Add** → **✅ Git Commit** → **⬆️ Push**

### 3️⃣ Gestionar Ramas

```
🧪 Nueva Rama → Crear rama experimental
🔀 Cambiar Rama → Cambiar a otra rama
   └─ Detección automática de divergencias
   └─ Opción de merge si hay diferencias
```

### 4️⃣ Resolver Conflictos de Merge

Si hay conflictos durante un merge:

```
⚠️ La interfaz mostrará:
├─ Lista de archivos en conflicto
├─ Botones para cada archivo:
│  ├─ "Ours" → Mantener versión actual
│  ├─ "Theirs" → Aceptar versión entrante
│  └─ "✏️ Editar" → Resolver manualmente en VS Code
└─ Una vez resueltos: "✅ Continuar Merge"
```

### 5️⃣ Crear Versiones (Tags)

```
🚀 Crear Tag → Etiquetar versión
🏷️ Gestionar Tags → Ver/Eliminar tags
⬆️ Push Tags → Subir tags al remoto
```

### 6️⃣ Análisis Avanzado

```
🔍 Analizar Divergencias → Comparar ramas manualmente
🕐 Ver Commits → Historial completo con detalles
📂 Commits x Archivo → Historial de un archivo específico
```

---

## 📸 Capturas de Pantalla

### Interfaz Principal
```
┌─────────────────────────────────────────────────────────┐
│ 📁 PROYECTO                                             │
│ C:/mi-proyecto  [📂][👨‍💻][🔁]                           │
├─────────────────────────────────────────────────────────┤
│ 🌿 Rama: main              [ℹ️ Info] [🔍 Analizar]     │
├─────────────────────────────────────────────────────────┤
│ 📂 ARCHIVOS DEL PROYECTO                                │
│                                                         │
│ [✓] index.js          [✅ Staged]                       │
│ [✓] package.json      [📝 Modificado]                   │
│ [ ] README.md         [💾 Committed (2025-11-28)]      │
│                                                         │
├─────────────────────────────────────────────────────────┤
│ ⚡ Básico  │ 🌿 Ramas  │ 🔧 Avanzado  │ 🌐 GitHub      │
└─────────────────────────────────────────────────────────┘
```

### Ventana de Divergencias
```
⚠️ Divergencia entre Ramas Detectada

Se detectaron 3 archivo(s) con commits diferentes
entre 'master' y 'feature/nueva-funcionalidad'

┌──────────────────────────────────────────────────────┐
│ Archivo    │ master      │ feature     │ Más reciente│
├──────────────────────────────────────────────────────┤
│ gui.py     │ abc123      │ def456      │ 🕐 feature  │
│            │ 21:22       │ 22:47       │             │
├──────────────────────────────────────────────────────┤
│ config.py  │ xyz789      │ uvw012      │ 🕐 master   │
│            │ 23:15       │ 20:30       │             │
└──────────────────────────────────────────────────────┘

[🔀 Fusionar feature → master] [📊 Historial] [✅ Continuar]
```

---

## 🎨 Personalización

### Cambiar Tema de Colores

En el código, busca la sección de configuración:

```python
ctk.set_appearance_mode("dark")  # "dark" o "light"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"
```

### Agregar Carpetas a Ignorar

Modifica el set `CARPETAS_IGNORADAS`:

```python
CARPETAS_IGNORADAS = {
    '.git', 'node_modules', 'venv', 'env', '.venv', '__pycache__',
    '.pytest_cache', '.mypy_cache', 'dist', 'build', '.next', '.nuxt',
    'target', 'vendor', '.idea', '.vscode',
    # Agregar aquí tus carpetas personalizadas
    'mi_carpeta_custom',
}
```

### Personalizar .gitignore Automático

Edita la variable `GITIGNORE_TEMPLATE`:

```python
GITIGNORE_TEMPLATE = """
# Tu template personalizado
*.log
*.tmp
"""
```

---

## 🛠️ Desarrollo

### Estructura del Proyecto

```
aetheryon-dev-core/
├── AETHERYON-Dev_Core_Customtkinter-Git.py  # Archivo principal
├── requirements.txt                          # Dependencias
├── README.md                                 # Este archivo
└── .gitignore                               # Archivos ignorados
```

### Arquitectura

```
┌─────────────────────────────────────────┐
│      AetheryonDevCoreApp (GUI)          │
│  ┌───────────────────────────────────┐  │
│  │                                   │  │
│  │   CustomTkinter Interface         │  │
│  │   ├─ Frames                       │  │
│  │   ├─ Buttons                      │  │
│  │   ├─ ScrollableFrames             │  │
│  │   └─ Dialogs                      │  │
│  │                                   │  │
│  └───────────────────────────────────┘  │
│              ↓↑                          │
│  ┌───────────────────────────────────┐  │
│  │      Proyecto (Git Logic)         │  │
│  │                                   │  │
│  │   GitPython Wrapper               │  │
│  │   ├─ Repository Management        │  │
│  │   ├─ Branch Operations            │  │
│  │   ├─ Commit History              │  │
│  │   ├─ Divergence Detection        │  │
│  │   └─ Merge Resolution            │  │
│  │                                   │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📝 Roadmap

- [ ] Soporte para Stash (guardar cambios temporalmente)
- [ ] Visualización gráfica del historial de commits
- [ ] Diff visual integrado con syntax highlighting
- [ ] Soporte para Git Rebase interactivo
- [ ] Gestión de remotes múltiples
- [ ] Integración con GitLab y Bitbucket
- [ ] Temas personalizables por el usuario
- [ ] Atajos de teclado configurables
- [ ] Modo "Zen" para commits (sin distracciones)
- [ ] Estadísticas de contribuciones

---

## ⚠️ Problemas Conocidos

### Error de merge-base
Si ves este error:
```
Error analizando merge: Cmd('git') failed due to: exit code(1)
```

**Solución**: Actualiza a la última versión donde se corrigió el orden de parámetros en `analizar_merge_previo()`.

### Divergencias no se muestran
Si las divergencias no aparecen automáticamente:
- Verifica que tengas commits diferentes en ambas ramas
- Usa el botón **🔍 Analizar Divergencias** manualmente
- Revisa los logs en la consola para debug

---

## 🤝 Créditos

Desarrollado con ❤️ por **Guido Gómez (Gúydal)**

Tecnologías utilizadas:
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) - Interfaz moderna
- [GitPython](https://github.com/gitpython-developers/GitPython) - Integración con Git
- [GitHub CLI](https://cli.github.com/) - Creación de repositorios

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

---

## 💬 Contacto

- **GitHub**: [@agraound](https://github.com/agraound)
- **Email**: contacto@agraound.site
- **Issues**: [Reportar un problema](https://github.com/agraound/git-devcore-customtkinter/issues)

---

<div align="center">

**¿Te gusta AETHERYON Dev Core?** ⭐ Dale una estrella en GitHub

[⬆ Volver arriba](#-aetheryon-dev-core---git-control-console)

</div>
