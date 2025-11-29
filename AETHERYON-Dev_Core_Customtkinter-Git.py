import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from git import Repo, GitCommandError
from datetime import datetime
import threading
import subprocess

# Configuración de CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

#-----------------------------------
# CONFIGURACIÓN DE CARPETAS A IGNORAR
#-----------------------------------

CARPETAS_IGNORADAS = {
    '.git', 'node_modules', 'venv', 'env', '.venv', '__pycache__',
    '.pytest_cache', '.mypy_cache', 'dist', 'build', '.next', '.nuxt',
    'target', 'vendor', '.idea', '.vscode',
}

GITIGNORE_TEMPLATE = """# Dependencias
node_modules/
venv/
env/
.venv/
__pycache__/
*.pyc
*.pyo
*.pyd

# Build & Distribución
dist/
build/
*.egg-info/
.next/
.nuxt/
target/

# IDEs
.idea/
.vscode/
*.swp
*.swo

# Sistema
.DS_Store
Thumbs.db
*.log

# Archivos de entorno
.env
.env.local
"""

#-----------------------------------
# Custom Dialogs
#-----------------------------------

class CTkInputDialog(ctk.CTkToplevel):
    def __init__(self, parent, title="", prompt="", initialvalue="", **kwargs):
        super().__init__(parent)
        self.parent = parent
        self.title(title)
        self.result = None
        
        self.transient(parent)
        self.grab_set()
        self.geometry("400x200")
        self._center_on_parent()
        
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.bind("<Escape>", lambda e: self._on_cancel())
        
        self._create_widgets(prompt, initialvalue, **kwargs)
        self.wait_window()
    
    def _center_on_parent(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (width // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (height // 2)
        self.geometry(f"+{x}+{y}")
    
    def _create_widgets(self, prompt, initialvalue, **kwargs):
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        if prompt:
            prompt_label = ctk.CTkLabel(main_frame, text=prompt, 
                                      font=("Arial", 12, "bold"))
            prompt_label.pack(pady=(10, 5))
        
        self.entry = ctk.CTkEntry(main_frame, font=("Arial", 11))
        self.entry.pack(fill="x", pady=10, padx=10)
        self.entry.insert(0, initialvalue)
        self.entry.bind("<Return>", lambda e: self._on_ok())
        self.entry.focus_set()
        
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=10)
        
        ctk.CTkButton(button_frame, text="✅ Aceptar", 
                     command=self._on_ok,
                     fg_color="green", width=120).pack(side="right", padx=5)
        ctk.CTkButton(button_frame, text="❌ Cancelar", 
                     command=self._on_cancel,
                     fg_color="gray", width=120).pack(side="right", padx=5)
    
    def _on_ok(self):
        self.result = self.entry.get()
        self.destroy()
    
    def _on_cancel(self):
        self.result = None
        self.destroy()

class CTkChoiceDialog(ctk.CTkToplevel):
    def __init__(self, parent, title="", prompt="", choices=None, **kwargs):
        super().__init__(parent)
        self.parent = parent
        self.title(title)
        self.result = None
        self.choices = choices or []
        
        self.transient(parent)
        self.grab_set()
        self.geometry("450x300")
        self._center_on_parent()
        
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.bind("<Escape>", lambda e: self._on_cancel())
        
        self._create_widgets(prompt, **kwargs)
        self.wait_window()
    
    def _center_on_parent(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (width // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (height // 2)
        self.geometry(f"+{x}+{y}")
    
    def _create_widgets(self, prompt, **kwargs):
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        if prompt:
            prompt_label = ctk.CTkLabel(main_frame, text=prompt, 
                                      font=("Arial", 12, "bold"))
            prompt_label.pack(pady=(10, 5))
        
        scroll_frame = ctk.CTkScrollableFrame(main_frame, height=150)
        scroll_frame.pack(fill="both", expand=True, pady=10, padx=10)
        
        self.choice_var = ctk.StringVar(value="")
        
        for choice in self.choices:
            radio = ctk.CTkRadioButton(scroll_frame, text=choice, 
                                     variable=self.choice_var, value=choice)
            radio.pack(anchor="w", pady=2)
        
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=10)
        
        ctk.CTkButton(button_frame, text="✅ Seleccionar", 
                     command=self._on_ok,
                     fg_color="green", width=120).pack(side="right", padx=5)
        ctk.CTkButton(button_frame, text="❌ Cancelar", 
                     command=self._on_cancel,
                     fg_color="gray", width=120).pack(side="right", padx=5)
    
    def _on_ok(self):
        self.result = self.choice_var.get()
        self.destroy()
    
    def _on_cancel(self):
        self.result = None
        self.destroy()

#-----------------------------------
# Clase Proyecto
#-----------------------------------

class Proyecto:
    def __init__(self, path):
        self.path = path
        self.repo = self._cargar_repo()

    def _cargar_repo(self):
        try:
            return Repo(self.path)
        except:
            return None

    def iniciar_git(self):
        if not os.path.exists(os.path.join(self.path, ".git")):
            self.repo = Repo.init(self.path)
            
            gitignore_path = os.path.join(self.path, ".gitignore")
            if not os.path.exists(gitignore_path):
                with open(gitignore_path, 'w', encoding='utf-8') as f:
                    f.write(GITIGNORE_TEMPLATE)
                print("📄 .gitignore creado automáticamente")
            
            return True
        return False

    def get_rama_actual(self):
        if not self.repo:
            return "Sin repo"
        try:
            return str(self.repo.active_branch)
        except:
            return "HEAD detached"

    def cambiar_rama(self, nombre_rama):
        try:
            self.repo.git.checkout(nombre_rama)
            return True
        except GitCommandError as e:
            return str(e)

    def listar_ramas(self):
        try:
            ramas_locales = [str(rama) for rama in self.repo.branches]
            try:
                ramas_remotas = [str(rama).replace('origin/', '') for rama in self.repo.remote().refs]
            except:
                ramas_remotas = []
            return {
                'locales': ramas_locales,
                'remotas': ramas_remotas
            }
        except Exception as e:
            return {'locales': [], 'remotas': []}

    def fetch(self):
        try:
            self.repo.git.fetch()
            return True
        except GitCommandError as e:
            return str(e)

    def cherry_pick_commit(self, commit_hash):
        try:
            self.repo.git.cherry_pick(commit_hash)
            return True
        except GitCommandError as e:
            return str(e)

    def crear_rama(self, nombre_rama):
        try:
            self.repo.git.checkout('HEAD', b=nombre_rama)
            return True
        except GitCommandError as e:
            return str(e)

#####MERGE
    def merge_rama(self, rama_origen):
        """Realiza un merge de la rama especificada a la rama actual"""
        try:
            self.repo.git.merge(rama_origen)
            return True
        except GitCommandError as e:
            return str(e)

    def abortar_merge(self):
        """Aborta un merge en progreso"""
        try:
            self.repo.git.merge('--abort')
            return True
        except GitCommandError as e:
            return str(e)

    def continuar_merge(self):
        """Continúa un merge después de resolver conflictos"""
        try:
            self.repo.git.commit('--no-edit')
            return True
        except GitCommandError as e:
            return str(e)

    def hay_merge_en_progreso(self):
        """Verifica si hay un merge en progreso"""
        merge_head = os.path.join(self.path, '.git', 'MERGE_HEAD')
        return os.path.exists(merge_head)

    def get_conflictos(self):
        """Obtiene la lista de archivos con conflictos"""
        if not self.repo:
            return []
        
        try:
            # Obtener archivos con conflictos usando git diff
            output = self.repo.git.diff('--name-only', '--diff-filter=U')
            if output:
                return output.strip().split('\n')
            return []
        except Exception as e:
            print(f"Error obteniendo conflictos: {e}")
            return []

    def resolver_conflicto_archivo(self, archivo, resolucion='ours'):
        """
        Resuelve un conflicto de merge para un archivo específico
        resolucion: 'ours' (mantener cambios actuales) o 'theirs' (aceptar cambios entrantes)
        """
        try:
            if resolucion == 'ours':
                self.repo.git.checkout('--ours', archivo)
            elif resolucion == 'theirs':
                self.repo.git.checkout('--theirs', archivo)
            
            self.repo.git.add(archivo)
            return True
        except GitCommandError as e:
            return str(e)



    def detectar_divergencia_ramas(self, rama1, rama2):
        """
        Detecta si dos ramas tienen commits diferentes (divergencia)
        Retorna dict con archivos divergentes y sus timestamps
        """
        if not self.repo:
            return None
        
        try:
            # Obtener commits de ambas ramas
            commits_rama1 = {}
            commits_rama2 = {}
            
            # Analizar rama1
            for commit in self.repo.iter_commits(rama1, max_count=50):
                for item in commit.stats.files.keys():
                    if item not in commits_rama1:
                        commits_rama1[item] = {
                            'hash': commit.hexsha[:8],
                            'fecha': datetime.fromtimestamp(commit.committed_date).strftime('%Y-%m-%d %H:%M'),
                            'timestamp': commit.committed_date,
                            'mensaje': commit.message.strip()
                        }
            
            # Analizar rama2
            for commit in self.repo.iter_commits(rama2, max_count=50):
                for item in commit.stats.files.keys():
                    if item not in commits_rama2:
                        commits_rama2[item] = {
                            'hash': commit.hexsha[:8],
                            'fecha': datetime.fromtimestamp(commit.committed_date).strftime('%Y-%m-%d %H:%M'),
                            'timestamp': commit.committed_date,
                            'mensaje': commit.message.strip()
                        }
            
            # Encontrar divergencias
            divergencias = {}
            todos_archivos = set(commits_rama1.keys()) | set(commits_rama2.keys())
            
            for archivo in todos_archivos:
                info1 = commits_rama1.get(archivo)
                info2 = commits_rama2.get(archivo)
                
                # Si el archivo existe en ambas ramas pero con diferentes commits
                if info1 and info2:
                    if info1['hash'] != info2['hash']:
                        divergencias[archivo] = {
                            rama1: info1,
                            rama2: info2,
                            'mas_reciente': rama1 if info1['timestamp'] > info2['timestamp'] else rama2,
                            'diferencia_dias': abs(info1['timestamp'] - info2['timestamp']) / 86400
                        }
                # Si el archivo solo existe en una rama
                elif info1 and not info2:
                    divergencias[archivo] = {
                        rama1: info1,
                        rama2: {'hash': 'N/A', 'fecha': 'No existe', 'mensaje': 'Archivo no presente'},
                        'solo_en': rama1
                    }
                elif info2 and not info1:
                    divergencias[archivo] = {
                        rama1: {'hash': 'N/A', 'fecha': 'No existe', 'mensaje': 'Archivo no presente'},
                        rama2: info2,
                        'solo_en': rama2
                    }
            
            return divergencias if divergencias else None
            
        except Exception as e:
            print(f"Error detectando divergencias: {e}")
            return None

    def analizar_merge_previo(self, rama_origen):
        """
        Analiza si un merge sería fast-forward o requiere commit de merge
        """
        try:
            rama_actual = self.get_rama_actual()
            
            # Ver si rama_actual está contenida en rama_origen (fast-forward posible)
            resultado = self.repo.git.merge_base('--is-ancestor', rama_actual, rama_origen)
            es_fast_forward = (resultado == '')
            
            # Contar commits diferentes
            commits_adelante = len(list(self.repo.iter_commits(f'{rama_actual}..{rama_origen}')))
            commits_atras = len(list(self.repo.iter_commits(f'{rama_origen}..{rama_actual}')))
            
            return {
                'es_fast_forward': es_fast_forward,
                'commits_adelante': commits_adelante,  # Cuántos commits tiene rama_origen que no tiene actual
                'commits_atras': commits_atras,        # Cuántos commits tiene actual que no tiene rama_origen
                'requiere_merge': commits_adelante > 0 and commits_atras > 0
            }
            
        except Exception as e:
            print(f"Error analizando merge: {e}")
            return None

    def get_contenido_archivo_en_rama(self, archivo, rama):
        """Obtiene el contenido de un archivo en una rama específica"""
        try:
            contenido = self.repo.git.show(f'{rama}:{archivo}')
            return contenido
        except Exception as e:
            return None


####

    def push(self):
        try:
            self.repo.git.push()
            return True
        except GitCommandError as e:
            return str(e)

    def pull(self):
        try:
            self.repo.git.pull()
            return True
        except GitCommandError as e:
            return str(e)

    def get_git_log(self, max_count=10):
        try:
            return self.repo.git.log('--oneline', max_count=max_count)
        except GitCommandError as e:
            return str(e)

    def get_git_status(self):
        try:
            return self.repo.git.status()
        except GitCommandError as e:
            return str(e)

    def clonar_repo(self, url, directorio_destino):
        try:
            print(f"📥 Clonando repositorio: {url}")
            print(f"📂 Destino: {directorio_destino}")
            
            parent_dir = os.path.dirname(directorio_destino)
            if not os.path.exists(parent_dir):
                os.makedirs(parent_dir)
            
            self.repo = Repo.clone_from(url, directorio_destino)
            self.path = directorio_destino
            print("✅ Repositorio clonado exitosamente")
            return True
            
        except Exception as e:
            print(f"❌ Error al clonar: {e}")
            return str(e)

    def get_commits_detallados(self, max_count=20):
        if not self.repo:
            return []
        
        try:
            commits = []
            for commit in self.repo.iter_commits(max_count=max_count):
                commits.append({
                    'hash': commit.hexsha[:8],
                    'hash_completo': commit.hexsha,
                    'mensaje': commit.message.strip(),
                    'autor': str(commit.author),
                    'fecha': datetime.fromtimestamp(commit.committed_date).strftime('%Y-%m-%d %H:%M:%S'),
                    'fecha_relativa': self._tiempo_relativo(commit.committed_date)
                })
            return commits
        except Exception as e:
            return []

    def _tiempo_relativo(self, timestamp):
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        commit_time = datetime.fromtimestamp(timestamp, timezone.utc)
        diff = now - commit_time
        
        if diff.days > 0:
            return f"hace {diff.days} día{'s' if diff.days > 1 else ''}"
        elif diff.seconds > 3600:
            horas = diff.seconds // 3600
            return f"hace {horas} hora{'s' if horas > 1 else ''}"
        elif diff.seconds > 60:
            minutos = diff.seconds // 60
            return f"hace {minutos} minuto{'s' if minutos > 1 else ''}"
        else:
            return "hace unos segundos"

    def get_commits_por_archivo(self, archivo, max_count=20):
        if not self.repo:
            return []
        
        try:
            commits = []
            for commit in self.repo.iter_commits(paths=archivo, max_count=max_count):
                cambios = []
                if commit.parents:
                    diffs = commit.parents[0].diff(commit, paths=archivo)
                    for diff in diffs:
                        if diff.change_type == 'A':
                            cambios.append("📄 Archivo creado")
                        elif diff.change_type == 'M':
                            cambios.append("✏️ Modificado")
                        elif diff.change_type == 'D':
                            cambios.append("🗑️ Eliminado")
                        elif diff.change_type == 'R':
                            cambios.append("📝 Renombrado")
                else:
                    cambios.append("📄 Commit inicial")
                
                commits.append({
                    'hash': commit.hexsha[:8],
                    'hash_completo': commit.hexsha,
                    'mensaje': commit.message.strip(),
                    'autor': str(commit.author),
                    'fecha': datetime.fromtimestamp(commit.committed_date).strftime('%Y-%m-%d %H:%M:%S'),
                    'fecha_relativa': self._tiempo_relativo(commit.committed_date),
                    'cambios': ' | '.join(cambios) if cambios else "Sin cambios"
                })
            return commits
        except Exception as e:
            print(f"Error obteniendo commits del archivo: {e}")
            return []

    def crear_tag(self, nombre_tag, mensaje="", commit_hash=None):
        try:
            if commit_hash:
                if mensaje:
                    self.repo.git.tag('-a', nombre_tag, '-m', mensaje, commit_hash)
                else:
                    self.repo.git.tag(nombre_tag, commit_hash)
            else:
                if mensaje:
                    self.repo.git.tag('-a', nombre_tag, '-m', mensaje)
                else:
                    self.repo.git.tag(nombre_tag)
            
            print(f"🏷️ Tag '{nombre_tag}' creado")
            return True
            
        except GitCommandError as e:
            return str(e)

    def get_tags(self):
        if not self.repo:
            return []
        
        try:
            tags_info = []
            for tag in self.repo.tags:
                try:
                    commit = tag.commit
                    
                    try:
                        tag_obj = self.repo.odb.info(tag.object.binsha)
                        mensaje_tag = tag.tag.message if hasattr(tag, 'tag') else ""
                    except:
                        mensaje_tag = ""
                    
                    tags_info.append({
                        'nombre': tag.name,
                        'hash': commit.hexsha[:8],
                        'hash_completo': commit.hexsha,
                        'mensaje_commit': commit.message.strip(),
                        'mensaje_tag': mensaje_tag,
                        'autor': str(commit.author),
                        'fecha': datetime.fromtimestamp(commit.committed_date).strftime('%Y-%m-%d %H:%M:%S'),
                        'fecha_relativa': self._tiempo_relativo(commit.committed_date)
                    })
                except Exception as e:
                    print(f"Error procesando tag {tag.name}: {e}")
                    continue
            
            tags_info.sort(key=lambda x: x['fecha'], reverse=True)
            return tags_info
            
        except Exception as e:
            print(f"Error obteniendo tags: {e}")
            return []

    def eliminar_tag(self, nombre_tag):
        try:
            self.repo.git.tag('-d', nombre_tag)
            print(f"🗑️ Tag '{nombre_tag}' eliminado")
            return True
        except GitCommandError as e:
            return str(e)

    def push_tags(self):
        try:
            self.repo.git.push('--tags')
            return True
        except GitCommandError as e:
            return str(e)

    def reset_to_commit(self, commit_hash, tipo="soft"):
        try:
            if tipo == "soft":
                self.repo.git.reset('--soft', commit_hash)
            elif tipo == "mixed":
                self.repo.git.reset('--mixed', commit_hash)
            elif tipo == "hard":
                self.repo.git.reset('--hard', commit_hash)
            
            print(f"🔄 Reset {tipo} a commit {commit_hash}")
            return True
            
        except GitCommandError as e:
            return str(e)

    def crear_repo_gh(self, nombre, visibilidad="private"):
        """Crea un repositorio en GitHub usando GitHub CLI"""
        try:
            os.chdir(self.path)
            print(f"📂 Cambiando a directorio: {self.path}")
            
            if not os.path.exists(os.path.join(self.path, ".git")):
                print("🚀 Inicializando repositorio Git local...")
                self.iniciar_git()
            
            if not self.repo:
                self.repo = Repo(self.path)
            
            status = subprocess.getoutput("git status --porcelain").strip()
            print(f"📋 Status actual: {status}")
            
            try:
                result = subprocess.getoutput("git log --oneline -1").strip()
                if not result:
                    print("📝 No hay commits, creando commit inicial...")
                    need_initial_commit = True
                else:
                    print(f"✅ Último commit: {result}")
                    need_initial_commit = False
            except:
                need_initial_commit = True
            
            if need_initial_commit or status:
                print("📝 Preparando archivos para commit...")
                
                readme_path = os.path.join(self.path, "README.md")
                if not os.path.exists(readme_path):
                    with open(readme_path, 'w', encoding='utf-8') as f:
                        f.write(f"# {nombre}\n\nProyecto creado con AETHERYON Dev Core\n")
                    print("📄 README.md creado")
                
                subprocess.run("git add .", shell=True, check=True)
                print("➕ Archivos añadidos al stage")
                
                commit_result = subprocess.run('git commit -m "Initial commit"', shell=True)
                if commit_result.returncode == 0:
                    print("✅ Commit inicial realizado")
                else:
                    print("⚠️ Error en commit o no hay cambios")
            
            print(f"🌐 Creando repositorio en GitHub: {nombre}")
            
            command = f'gh repo create {nombre} --{visibilidad} --source=. --remote=origin --push'
            print(f"🔧 Ejecutando: {command}")
            
            result = subprocess.run(command, shell=True)
            
            if result.returncode == 0:
                print("✅ Repositorio GitHub creado exitosamente")
                self.repo = Repo(self.path)
                return True
            else:
                error_msg = f"Error ejecutando GitHub CLI (código: {result.returncode}).\n"
                
                if result.returncode == 1:
                    error_msg += "Posible causa: El repositorio ya existe o hay un problema de autenticación."
                elif result.returncode == 2:
                    error_msg += "Posible causa: Problema con los parámetros del comando."
                else:
                    error_msg += "Verifica que 'gh' esté instalado y autenticado correctamente."
                
                return error_msg
                
        except Exception as e:
            print(f"❌ Error en crear_repo_gh: {e}")
            return str(e)

    def estado_archivos(self):
        if not self.repo:
            return {}

        unstaged = []
        staged = []
        untracked = []

        try:
            untracked = self.repo.untracked_files
            untracked = [f for f in untracked if not self._esta_en_carpeta_ignorada(f)]
        except Exception as e:
            print(f"Error obteniendo untracked: {e}")
            untracked = []

        try:
            unstaged = [item.a_path for item in self.repo.index.diff(None)]
            unstaged = [f for f in unstaged if not self._esta_en_carpeta_ignorada(f)]
        except Exception as e:
            print(f"Error obteniendo unstaged: {e}")
            unstaged = []

        try:
            if self.repo.head.is_valid():
                staged = [item.a_path for item in self.repo.index.diff("HEAD")]
            else:
                staged = [item[0] for item in self.repo.index.entries.keys()]
            staged = [f for f in staged if not self._esta_en_carpeta_ignorada(f)]
        except Exception as e:
            print(f"Error obteniendo staged: {e}")
            try:
                staged = [item[0] for item in self.repo.index.entries.keys()]
                staged = [f for f in staged if not self._esta_en_carpeta_ignorada(f)]
            except:
                staged = []

        print(f"📊 Estado Git (filtrado):")
        print(f"  🆕 Untracked: {len(untracked)} archivos")
        print(f"  📝 Unstaged: {len(unstaged)} archivos")
        print(f"  ✅ Staged: {len(staged)} archivos")

        return {
            "unstaged": unstaged,
            "staged": staged,
            "untracked": untracked
        }

    def _esta_en_carpeta_ignorada(self, ruta):
        partes = ruta.split('/')
        return any(carpeta in CARPETAS_IGNORADAS for carpeta in partes)

    def git_add(self, archivos):
        try:
            for archivo in archivos:
                self.repo.git.add(archivo)
            return True
        except GitCommandError as e:
            return str(e)

    def git_commit(self, mensaje):
        try:
            self.repo.git.commit('-m', mensaje)
            return True
        except GitCommandError as e:
            return str(e)

#########################

    def verificar_cambios_pendientes(self):
        """
        Verifica si hay cambios sin guardar en el working directory
        
        Returns:
            dict: {
                'tiene_cambios': bool,
                'unstaged': int,
                'untracked': int,
                'staged': int,
                'detalles': list[str]
            }
        """
        if not self.repo:
            return {
                'tiene_cambios': False,
                'unstaged': 0,
                'untracked': 0,
                'staged': 0,
                'detalles': []
            }
        
        try:
            detalles = []
            
            # Archivos modificados pero no staged
            unstaged_items = list(self.repo.index.diff(None))
            unstaged = len(unstaged_items)
            if unstaged > 0:
                detalles.append(f"📝 {unstaged} archivo(s) modificado(s)")
            
            # Archivos sin trackear
            untracked_files = self.repo.untracked_files
            untracked = len(untracked_files)
            if untracked > 0:
                detalles.append(f"🆕 {untracked} archivo(s) nuevo(s)")
            
            # Archivos staged pero no commiteados
            try:
                if self.repo.head.is_valid():
                    staged_items = list(self.repo.index.diff("HEAD"))
                    staged = len(staged_items)
                    if staged > 0:
                        detalles.append(f"✅ {staged} archivo(s) en stage")
                else:
                    staged = 0
            except:
                staged = 0
            
            tiene_cambios = unstaged > 0 or untracked > 0 or staged > 0
            
            return {
                'tiene_cambios': tiene_cambios,
                'unstaged': unstaged,
                'untracked': untracked,
                'staged': staged,
                'detalles': detalles
            }
        except Exception as e:
            print(f"Error verificando cambios: {e}")
            return {
                'tiene_cambios': False,
                'unstaged': 0,
                'untracked': 0,
                'staged': 0,
                'detalles': []
            }

    def stash_cambios(self, mensaje="Auto-stash antes de cambiar rama"):
        """
        Guarda cambios temporalmente en stash
        
        Args:
            mensaje: Mensaje descriptivo del stash
            
        Returns:
            True si exitoso, str con error si falla
        """
        try:
            # Verificar si hay algo que hacer stash
            info_cambios = self.verificar_cambios_pendientes()
            if not info_cambios['tiene_cambios']:
                return True  # No hay nada que guardar
            
            # Stash con mensaje
            self.repo.git.stash('push', '-u', '-m', mensaje)  # -u incluye untracked
            print(f"📦 Stash creado: {mensaje}")
            return True
        except GitCommandError as e:
            return f"Error al hacer stash: {str(e)}"

    def aplicar_stash(self, index=0, eliminar_despues=True):
        """
        Aplica un stash guardado
        
        Args:
            index: Índice del stash (0 es el más reciente)
            eliminar_despues: Si True usa 'pop', si False usa 'apply'
            
        Returns:
            True si exitoso, str con error si falla
        """
        try:
            if index == 0 and eliminar_despues:
                self.repo.git.stash('pop')
            elif eliminar_despues:
                self.repo.git.stash('pop', f'stash@{{{index}}}')
            else:
                self.repo.git.stash('apply', f'stash@{{{index}}}')
            
            print(f"✅ Stash aplicado (índice: {index})")
            return True
        except GitCommandError as e:
            return f"Error al aplicar stash: {str(e)}"

    def listar_stashes(self):
        """
        Lista todos los stashes disponibles
        
        Returns:
            list[dict]: Lista de stashes con info estructurada
        """
        try:
            stashes = []
            stash_list = self.repo.git.stash('list').split('\n')
            
            for i, stash_str in enumerate(stash_list):
                if stash_str.strip():
                    # Parsear formato: stash@{0}: WIP on branch: mensaje
                    parts = stash_str.split(': ', 2)
                    if len(parts) >= 3:
                        stashes.append({
                            'index': i,
                            'ref': parts[0],
                            'tipo': parts[1],
                            'mensaje': parts[2] if len(parts) > 2 else '',
                            'texto_completo': stash_str
                        })
                    else:
                        stashes.append({
                            'index': i,
                            'ref': f'stash@{{{i}}}',
                            'tipo': 'WIP',
                            'mensaje': stash_str,
                            'texto_completo': stash_str
                        })
            
            return stashes
        except Exception as e:
            print(f"Error listando stashes: {e}")
            return []

    def eliminar_stash(self, index):
        """Elimina un stash específico"""
        try:
            self.repo.git.stash('drop', f'stash@{{{index}}}')
            print(f"🗑️ Stash {index} eliminado")
            return True
        except GitCommandError as e:
            return f"Error al eliminar stash: {str(e)}"

    def cambiar_rama_seguro(self, nombre_rama, forzar=False, stash_automatico=False):
        """
        Cambia de rama de forma segura, verificando el estado del working directory
        
        Args:
            nombre_rama: Nombre de la rama destino
            forzar: Si es True, fuerza el checkout descartando cambios locales
            stash_automatico: Si es True, hace stash automático de cambios
        
        Returns:
            dict con resultado detallado
        """
        try:
            rama_origen = self.get_rama_actual()
            
            # Verificar si ya estamos en esa rama
            if rama_origen == nombre_rama:
                return {
                    'exito': True,
                    'mensaje': f'Ya estás en la rama {nombre_rama}',
                    'cambios_pendientes': False,
                    'rama_actual': rama_origen,
                    'sin_cambios': True
                }
            
            # Verificar si hay cambios pendientes
            info_cambios = self.verificar_cambios_pendientes()
            tiene_cambios = info_cambios['tiene_cambios']
            
            # Manejar cambios pendientes
            if tiene_cambios:
                if stash_automatico:
                    # Hacer stash automático
                    resultado_stash = self.stash_cambios(
                        f"Auto-stash: cambio de {rama_origen} a {nombre_rama}"
                    )
                    if resultado_stash != True:
                        return {
                            'exito': False,
                            'mensaje': 'Error al hacer stash automático',
                            'cambios_pendientes': True,
                            'error': resultado_stash
                        }
                    print("📦 Cambios guardados automáticamente en stash")
                elif not forzar:
                    # Requiere acción del usuario
                    return {
                        'exito': False,
                        'mensaje': 'Hay cambios sin guardar',
                        'cambios_pendientes': True,
                        'requiere_stash': True,
                        'info_cambios': info_cambios
                    }
            
            # Realizar el checkout
            if forzar:
                # Checkout forzado (descarta cambios locales)
                print(f"⚠️ Checkout FORZADO a {nombre_rama} (descartando cambios)")
                self.repo.git.checkout(nombre_rama, force=True)
            else:
                # Checkout normal
                print(f"🔀 Checkout a {nombre_rama}")
                self.repo.git.checkout(nombre_rama)
            
            # Verificar que el checkout fue exitoso
            rama_actual = self.get_rama_actual()
            checkout_exitoso = (rama_actual == nombre_rama)
            
            if checkout_exitoso:
                print(f"✅ Cambio exitoso: {rama_origen} → {rama_actual}")
                return {
                    'exito': True,
                    'mensaje': f'Cambiado exitosamente a {nombre_rama}',
                    'cambios_pendientes': False,
                    'rama_origen': rama_origen,
                    'rama_actual': rama_actual,
                    'habia_cambios': tiene_cambios,
                    'stash_aplicado': stash_automatico and tiene_cambios
                }
            else:
                return {
                    'exito': False,
                    'mensaje': f'El checkout no se completó correctamente (rama actual: {rama_actual})',
                    'cambios_pendientes': False,
                    'rama_actual': rama_actual
                }
                
        except GitCommandError as e:
            error_msg = str(e)
            
            # Analizar el tipo de error
            if "would be overwritten" in error_msg:
                return {
                    'exito': False,
                    'mensaje': 'Archivos modificados serían sobrescritos',
                    'cambios_pendientes': True,
                    'requiere_stash': True,
                    'error': error_msg,
                    'tipo_error': 'conflicto_archivos'
                }
            elif "does not exist" in error_msg:
                return {
                    'exito': False,
                    'mensaje': f'La rama {nombre_rama} no existe',
                    'error': error_msg,
                    'tipo_error': 'rama_inexistente'
                }
            else:
                return {
                    'exito': False,
                    'mensaje': f'Error en checkout: {error_msg}',
                    'error': error_msg,
                    'tipo_error': 'desconocido'
                }
        except Exception as e:
            return {
                'exito': False,
                'mensaje': f'Error inesperado: {str(e)}',
                'error': str(e),
                'tipo_error': 'excepcion'
            }

#########################



#-----------------------------------
# Clase Principal
#-----------------------------------

class AetheryonDevCoreApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🧠 AETHERYON Dev Core - Git Control Console")
        self.root.geometry("1080x800")
        
        self.root.attributes('-topmost', True)
        self.root.after(100, lambda: self.root.attributes('-topmost', False))

        self.proyecto = None
        self.path_var = ctk.StringVar()
        self.url_clone_var = ctk.StringVar()
        self.archivos_data = {}
        self.rama_actual_var = ctk.StringVar(value="🌿 Rama: Sin repo")
        self.lista_archivos = []
        self.archivos_ignorados_count = 0

        self.setup_ui()

    def setup_ui(self):
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # SECCIÓN 1: PROYECTO
        frame_proyecto = ctk.CTkFrame(main_frame, fg_color="#1E3A5F")
        frame_proyecto.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(frame_proyecto, text="📁 PROYECTO", font=("Arial", 11, "bold")).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        entry_path = ctk.CTkEntry(frame_proyecto, textvariable=self.path_var, width=500)
        entry_path.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        ctk.CTkButton(frame_proyecto, text="📂 Seleccionar", command=self.seleccionar_directorio, 
                     width=110, fg_color="#2E7D32").grid(row=0, column=2, padx=3, pady=5)
        ctk.CTkButton(frame_proyecto, text="👨‍💻 VS Code", command=self.abrir_vscode, 
                     width=100, fg_color="#007ACC").grid(row=0, column=3, padx=3, pady=5)
        ctk.CTkButton(frame_proyecto, text="🔁 Refrescar", command=self.ver_archivos, 
                     width=100, fg_color="#00897B").grid(row=0, column=4, padx=3, pady=5)
        


        frame_proyecto.columnconfigure(1, weight=1)
        
        # SECCIÓN 2: CLONAR
        frame_clone = ctk.CTkFrame(main_frame, fg_color="#2B2B2B")
        frame_clone.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(frame_clone, text="🔗 CLONAR", font=("Arial", 11, "bold")).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        entry_url = ctk.CTkEntry(frame_clone, textvariable=self.url_clone_var, width=600, 
                                placeholder_text="https://github.com/usuario/repositorio.git")
        entry_url.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        ctk.CTkButton(frame_clone, text="📥 Clonar Repositorio", command=self.clonar_repositorio, 
                     fg_color="#00695C", hover_color="#004D40", width=150).grid(row=0, column=2, padx=5, pady=5)
        
        frame_clone.columnconfigure(1, weight=1)

        # SECCIÓN 3: RAMA ACTUAL
        frame_rama = ctk.CTkFrame(main_frame, fg_color="#1E3A5F")
        frame_rama.pack(fill="x", padx=5, pady=5)
        self.label_rama = ctk.CTkLabel(frame_rama, textvariable=self.rama_actual_var, 
                                       font=("Arial", 13, "bold"), text_color="white")
        self.label_rama.pack(side="left", padx=10, pady=8)
        
        ctk.CTkButton(frame_rama, text="ℹ️ Info de Rama", 
                    command=self.verificar_rama_y_archivos,
                    fg_color="#00695C", width=120, height=30,
                    font=("Arial", 10)).pack(side="left", padx=10)

        ctk.CTkButton(frame_rama, text="🔍 Analizar Divergencias", 
                    command=self.analizar_divergencias_manual,
                    fg_color="#E65100", width=160, height=30,
                    font=("Arial", 10)).pack(side="left", padx=10)

        # SECCIÓN 4: ARCHIVOS
        frame_archivos = ctk.CTkFrame(main_frame)
        frame_archivos.pack(fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(frame_archivos, text="📂 ARCHIVOS DEL PROYECTO", 
                    font=("Arial", 14, "bold")).pack(pady=5)
        
        self.scrollable_frame = ctk.CTkScrollableFrame(frame_archivos, width=1000, height=280)
        self.scrollable_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # SECCIÓN 5: BOTONES ORGANIZADOS
        tabview = ctk.CTkTabview(main_frame, height=120)
        tabview.pack(fill="x", padx=5, pady=5)
        
        # TAB 1: Operaciones Básicas
        tab_basico = tabview.add("⚡ Básico")
        frame_basico = ctk.CTkFrame(tab_basico, fg_color="transparent")
        frame_basico.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkButton(frame_basico, text="🚀 Iniciar Git", command=self.iniciar_git, 
                     fg_color="#FF6F00", width=120, height=35).grid(row=0, column=0, padx=3, pady=3)
        ctk.CTkButton(frame_basico, text="➕ Git Add", command=self.git_add, 
                     fg_color="#FFB300", text_color="black", width=120, height=35).grid(row=0, column=1, padx=3, pady=3)
        ctk.CTkButton(frame_basico, text="✅ Git Commit", command=self.git_commit, 
                     fg_color="#00897B", width=120, height=35).grid(row=0, column=2, padx=3, pady=3)
        ctk.CTkButton(frame_basico, text="🔍 Estado", command=self.ver_status, 
                     fg_color="#546E7A", width=120, height=35).grid(row=0, column=3, padx=3, pady=3)
        ctk.CTkButton(frame_basico, text="📜 Ver Log", command=self.ver_log, 
                     fg_color="#5D4037", width=120, height=35).grid(row=0, column=4, padx=3, pady=3)


        # TAB 2: Ramas y Remotos
        tab_ramas = tabview.add("🌿 Ramas & Remotos")
        frame_ramas = ctk.CTkFrame(tab_ramas, fg_color="transparent")
        frame_ramas.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkButton(frame_ramas, text="🧪 Nueva Rama", command=self.nueva_rama, 
                     fg_color="#7B1FA2", width=130, height=35).grid(row=0, column=0, padx=3, pady=3)
        ctk.CTkButton(frame_ramas, text="🔀 Cambiar Rama", command=self.cambiar_rama, 
                     fg_color="#6A1B9A", width=130, height=35).grid(row=0, column=1, padx=3, pady=3)
        ctk.CTkButton(frame_ramas, text="⬆️ Push", command=self.push, 
                     fg_color="#C62828", width=110, height=35).grid(row=0, column=2, padx=3, pady=3)
        ctk.CTkButton(frame_ramas, text="⬇️ Pull", command=self.pull, 
                     fg_color="#1565C0", width=110, height=35).grid(row=0, column=3, padx=3, pady=3)
        ctk.CTkButton(frame_ramas, text="🔄 Fetch", command=self.fetch, 
                     fg_color="#0277BD", width=110, height=35).grid(row=0, column=4, padx=3, pady=3)
        ctk.CTkButton(frame_ramas, text="🔀 Merge", command=self.merge_ramas, 
                     fg_color="#7B1FA2", width=110, height=35).grid(row=0, column=5, padx=3, pady=3)


        # TAB 3: Historial y Avanzado
        tab_avanzado = tabview.add("🔧 Avanzado")
        frame_avanzado = ctk.CTkFrame(tab_avanzado, fg_color="transparent")
        frame_avanzado.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkButton(frame_avanzado, text="🕐 Ver Commits", command=self.ver_commits_detallados, 
                     fg_color="#2E7D32", width=130, height=35).grid(row=0, column=0, padx=3, pady=3)
        ctk.CTkButton(frame_avanzado, text="🍒 Cherry Pick", command=self.cherry_pick, 
                     fg_color="#D32F2F", width=130, height=35).grid(row=0, column=1, padx=3, pady=3)
        ctk.CTkButton(frame_avanzado, text="📂 Commits x Archivo", command=self.ver_commits_por_archivo, 
                     fg_color="#283593", width=150, height=35).grid(row=0, column=2, padx=3, pady=3)
        ctk.CTkButton(frame_avanzado, text="🏷️ Gestionar Tags", command=self.gestionar_tags, 
                     fg_color="#E65100", width=140, height=35).grid(row=0, column=3, padx=3, pady=3)
        ctk.CTkButton(frame_avanzado, text="🚀 Crear Tag", command=self.crear_tag_version, 
                     fg_color="#BF360C", width=110, height=35).grid(row=0, column=4, padx=3, pady=3)
        ctk.CTkButton(frame_ramas, text="🔀 Merge", command=self.merge_ramas, 
                     fg_color="#7B1FA2", width=110, height=35).grid(row=0, column=5, padx=3, pady=3)
        ctk.CTkButton(frame_ramas, text="📦 Stashes", command=self.gestionar_stashes,
                     fg_color="#FF6F00", width=110, height=35).grid(row=0, column=6, padx=3, pady=3)


        # TAB 4: GitHub
        tab_github = tabview.add("🌐 GitHub")
        frame_github = ctk.CTkFrame(tab_github, fg_color="transparent")
        frame_github.pack(expand=True)
        
        ctk.CTkButton(frame_github, text="🌐 Crear Repositorio en GitHub", command=self.crear_repo_github, 
                     fg_color="#24292e", hover_color="#0366d6", 
                     font=("Arial", 13, "bold"), height=45, width=300).pack(pady=20)

    # ==================== MÉTODOS PRINCIPALES ====================

    def analizar_divergencias_manual(self):
        """Permite analizar divergencias entre dos ramas manualmente"""
        if not self.proyecto or not self.proyecto.repo:
            messagebox.showwarning("Sin Git", "No hay repositorio Git inicializado.")
            return
        
        ramas_info = self.proyecto.listar_ramas()
        ramas = ramas_info.get('locales', [])
        
        if len(ramas) < 2:
            messagebox.showinfo("Pocas ramas", "Necesitás al menos 2 ramas para analizar divergencias.")
            return
        
        rama_actual = self.proyecto.get_rama_actual()
        
        # Seleccionar rama para comparar
        dialog = CTkChoiceDialog(
            parent=self.root,
            title="🔍 Analizar Divergencias",
            prompt=f"Comparar rama actual ({rama_actual}) con:",
            choices=[r for r in ramas if r != rama_actual]
        )
        
        rama_comparar = dialog.result
        
        if not rama_comparar:
            return
        
        print(f"🔍 Analizando divergencias: {rama_actual} vs {rama_comparar}")
        
        divergencias = self.proyecto.detectar_divergencia_ramas(rama_actual, rama_comparar)
        
        if divergencias:
            self._mostrar_analisis_divergencias(rama_actual, rama_comparar, divergencias)
        else:
            messagebox.showinfo("Sin divergencias", 
                f"✅ No se encontraron divergencias entre:\n\n"
                f"• {rama_actual}\n"
                f"• {rama_comparar}\n\n"
                "Las ramas están sincronizadas.")



    def seleccionar_directorio(self):
        ruta = filedialog.askdirectory()
        if ruta:
            self.path_var.set(ruta)
            self.proyecto = Proyecto(ruta)
            self.actualizar_rama_display()
            print(f"📁 Proyecto seleccionado: {ruta}")
            self.ver_archivos()

    def actualizar_rama_display(self):
        if self.proyecto:
            rama = self.proyecto.get_rama_actual()
            self.rama_actual_var.set(f"🌿 Rama: {rama}")
            
            # Actualizar título de la ventana con la rama actual
            self.root.title(f"🧠 AETHERYON Dev Core - Git Control Console  |  🌿 {rama}")
        else:
            self.rama_actual_var.set("🌿 Rama: Sin repo")
            self.root.title("🧠 AETHERYON Dev Core - Git Control Console")

    def abrir_vscode(self):
        path = self.path_var.get()
        if not path:
            messagebox.showwarning("Sin proyecto", "Primero seleccioná un directorio de proyecto.")
            return
        
        if not self.proyecto or not self.proyecto.repo:
            respuesta = messagebox.askyesno("Sin Git", 
                "Este directorio no tiene un repositorio Git.\n"
                "¿Querés inicializar uno antes de abrir VS Code?")
            if respuesta:
                self.proyecto = Proyecto(path)
                self.proyecto.iniciar_git()
                self.actualizar_rama_display()
        
        # Mostrar información de la rama antes de abrir
        if self.proyecto and self.proyecto.repo:
            rama_actual = self.proyecto.get_rama_actual()
            
            ventana_info = ctk.CTkToplevel(self.root)
            ventana_info.title("👨‍💻 Abriendo VS Code")
            ventana_info.geometry("500x300")
            ventana_info.transient(self.root)
            ventana_info.attributes('-topmost', True)
            ventana_info.grab_set()
            
            ctk.CTkLabel(ventana_info, text="👨‍💻 VS Code", 
                        font=("Arial", 16, "bold")).pack(pady=20)
            
            info_frame = ctk.CTkFrame(ventana_info, fg_color="#1E3A5F")
            info_frame.pack(fill="x", padx=20, pady=10)
            
            ctk.CTkLabel(info_frame, text=f"📁 Proyecto: {os.path.basename(path)}", 
                        font=("Arial", 11)).pack(pady=5, padx=10)
            
            ctk.CTkLabel(info_frame, text=f"🌿 Rama activa: {rama_actual}", 
                        font=("Arial", 12, "bold"), 
                        text_color="#90EE90").pack(pady=5, padx=10)
            
            ctk.CTkLabel(ventana_info, 
                        text="⚠️ RECORDATORIO IMPORTANTE:\n\n"
                            "Los archivos que edites en VS Code\n"
                            f"se modificarán en la rama: {rama_actual}\n\n"
                            "Si querés editar en otra rama,\n"
                            "PRIMERO cambiá de rama en esta consola.", 
                        font=("Arial", 10), 
                        text_color="orange",
                        justify="center").pack(pady=15)
            
            def abrir_editor():
                ventana_info.destroy()
                try:
                    os.system(f'code "{path}"')
                    print(f"👨‍💻 Abriendo VS Code en: {path}")
                    print(f"🌿 Rama activa: {rama_actual}")
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo abrir VS Code:\n{e}")
            
            button_frame = ctk.CTkFrame(ventana_info, fg_color="transparent")
            button_frame.pack(pady=10)
            
            ctk.CTkButton(button_frame, text="✅ Abrir VS Code", 
                        command=abrir_editor,
                        fg_color="#007ACC", width=150, height=35,
                        font=("Arial", 11, "bold")).pack(side="left", padx=5)
            
            ctk.CTkButton(button_frame, text="🔀 Cambiar Rama Primero", 
                        command=lambda: [ventana_info.destroy(), self.cambiar_rama()],
                        fg_color="#7B1FA2", width=160, height=35).pack(side="left", padx=5)
            
            ctk.CTkButton(button_frame, text="❌ Cancelar", 
                        command=ventana_info.destroy,
                        fg_color="gray", width=100, height=35).pack(side="left", padx=5)
        else:
            try:
                os.system(f'code "{path}"')
                print(f"👨‍💻 Abriendo en VS Code: {path}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir VS Code:\n{e}")

    def verificar_rama_y_archivos(self):
        """Muestra información detallada de la rama actual y archivos modificados"""
        if not self.proyecto or not self.proyecto.repo:
            messagebox.showwarning("Sin Git", "No hay repositorio Git inicializado.")
            return
        
        rama_actual = self.proyecto.get_rama_actual()
        git_estado = self.proyecto.estado_archivos()
        
        ventana_info = ctk.CTkToplevel(self.root)
        ventana_info.title(f"🌿 Información de Rama: {rama_actual}")
        ventana_info.geometry("700x550")
        ventana_info.transient(self.root)
        ventana_info.attributes('-topmost', True)
        
        ctk.CTkLabel(ventana_info, text="🌿 Estado de la Rama Actual", 
                    font=("Arial", 16, "bold")).pack(pady=15)
        
        # Información de la rama
        info_frame = ctk.CTkFrame(ventana_info, fg_color="#1E3A5F")
        info_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(info_frame, text=f"📍 Rama activa: {rama_actual}", 
                    font=("Arial", 13, "bold"), 
                    text_color="#90EE90").pack(pady=8, padx=10)
        
        ctk.CTkLabel(info_frame, 
                    text="Cualquier cambio que hagas en tus archivos\n"
                        "se aplicará a esta rama.", 
                    font=("Arial", 10), 
                    text_color="#87CEEB").pack(pady=5, padx=10)
        
        # Estadísticas
        stats_frame = ctk.CTkFrame(ventana_info, fg_color="#2B2B2B")
        stats_frame.pack(fill="x", padx=20, pady=10)
        
        untracked = len(git_estado.get("untracked", []))
        unstaged = len(git_estado.get("unstaged", []))
        staged = len(git_estado.get("staged", []))
        
        stats_text = f"📊 Estado de archivos en esta rama:\n\n"
        stats_text += f"🆕 Archivos nuevos: {untracked}\n"
        stats_text += f"📝 Archivos modificados: {unstaged}\n"
        stats_text += f"✅ Archivos en stage: {staged}"
        
        ctk.CTkLabel(stats_frame, text=stats_text, 
                    font=("Arial", 11), 
                    justify="left").pack(pady=10, padx=15)
        
        # Últimos commits
        try:
            commits = self.proyecto.get_commits_detallados(5)
            if commits:
                ctk.CTkLabel(ventana_info, text="📜 Últimos 5 commits en esta rama:", 
                            font=("Arial", 12, "bold")).pack(pady=10)
                
                scroll_commits = ctk.CTkScrollableFrame(ventana_info, width=650, height=180)
                scroll_commits.pack(pady=5, padx=20)
                
                for commit in commits:
                    commit_frame = ctk.CTkFrame(scroll_commits, fg_color="#1E1E1E")
                    commit_frame.pack(fill="x", pady=2)
                    
                    ctk.CTkLabel(commit_frame, text=commit['hash'], 
                                font=("Courier", 9), width=80).pack(side="left", padx=5)
                    
                    mensaje = commit['mensaje'][:50] + "..." if len(commit['mensaje']) > 50 else commit['mensaje']
                    ctk.CTkLabel(commit_frame, text=mensaje, 
                                font=("Arial", 9), width=350, anchor="w").pack(side="left", padx=5)
                    
                    ctk.CTkLabel(commit_frame, text=commit['fecha_relativa'], 
                                font=("Arial", 9), width=120, 
                                text_color="#87CEEB").pack(side="left", padx=5)
        except Exception as e:
            print(f"Error obteniendo commits: {e}")
        
        # Botones de acción
        button_frame = ctk.CTkFrame(ventana_info, fg_color="transparent")
        button_frame.pack(pady=15)
        
        ctk.CTkButton(button_frame, text="🔀 Cambiar de Rama", 
                    command=lambda: [ventana_info.destroy(), self.cambiar_rama()],
                    fg_color="#7B1FA2", width=150).pack(side="left", padx=5)
        
        ctk.CTkButton(button_frame, text="👨‍💻 Abrir VS Code", 
                    command=lambda: [ventana_info.destroy(), self.abrir_vscode()],
                    fg_color="#007ACC", width=150).pack(side="left", padx=5)
        
        ctk.CTkButton(button_frame, text="❌ Cerrar", 
                    command=ventana_info.destroy,
                    fg_color="gray", width=100).pack(side="left", padx=5)

    def iniciar_git(self):
        if not self.proyecto:
            messagebox.showwarning("Sin proyecto", "Primero seleccioná un directorio de proyecto.")
            return
        
        if self.proyecto.iniciar_git():
            messagebox.showinfo("Git inicializado", 
                "✅ Repositorio Git inicializado correctamente.\n\n"
                "📄 Se creó automáticamente un .gitignore que excluye:\n"
                "• node_modules/\n"
                "• venv/ y entornos virtuales\n"
                "• __pycache__/\n"
                "• Carpetas de build\n"
                "• Y más...")
            self.actualizar_rama_display()
            self.ver_archivos()
        else:
            messagebox.showinfo("Git ya existe", "El repositorio Git ya está inicializado.")

    def ver_archivos(self):
        if not self.proyecto:
            messagebox.showwarning("Sin proyecto", "Primero seleccioná un directorio de proyecto.")
            return

        path = self.proyecto.path
        
        if not self.proyecto.repo:
            respuesta = messagebox.askyesno("Sin Git", 
                "Este directorio no tiene un repositorio Git. ¿Querés inicializar uno?")
            if respuesta:
                self.proyecto.iniciar_git()
            else:
                return

        print("=" * 60)
        print("📂 Escaneando archivos (ignorando dependencias)...")
        print("=" * 60)
        
        git_estado = self.proyecto.estado_archivos()
        
        self.lista_archivos.clear()
        self.archivos_data.clear()
        self.archivos_ignorados_count = 0

        archivos_encontrados = []
        for root_dir, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in CARPETAS_IGNORADAS]
            
            for file in files:
                abs_path = os.path.join(root_dir, file)
                rel_path = os.path.relpath(abs_path, path).replace('\\', '/')
                
                if self._archivo_en_carpeta_ignorada(rel_path):
                    self.archivos_ignorados_count += 1
                    continue
                
                archivos_encontrados.append(rel_path)

        for rel_path in archivos_encontrados:
            estado = self._determinar_estado_archivo(rel_path, git_estado)
            self.lista_archivos.append((rel_path, estado))
            print(f"  → {rel_path:<50} [{estado}]")

        print("=" * 60)
        print(f"✅ Archivos visibles: {len(self.lista_archivos)}")
        print(f"🚫 Archivos ignorados: {self.archivos_ignorados_count}")
        print("=" * 60)
        
        self.actualizar_lista_archivos()

    def _archivo_en_carpeta_ignorada(self, ruta):
        partes = ruta.split('/')
        return any(carpeta in CARPETAS_IGNORADAS for carpeta in partes)

    def _determinar_estado_archivo(self, rel_path, git_estado):
        if rel_path in git_estado.get("untracked", []):
            return "🆕 Untracked"
        elif rel_path in git_estado.get("unstaged", []):
            return "📝 Modificado"
        elif rel_path in git_estado.get("staged", []):
            return "✅ Staged"
        else:
            try:
                if self.proyecto.repo and self.proyecto.repo.head.is_valid():
                    commits = list(self.proyecto.repo.iter_commits(paths=rel_path, max_count=1))
                    if commits:
                        fecha = datetime.fromtimestamp(commits[0].committed_date).strftime('%Y-%m-%d %H:%M')
                        return f"💾 Committed ({fecha})"
                return "📄 Sin cambios"
            except:
                return "❓ Desconocido"

    def actualizar_lista_archivos(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        if not self.lista_archivos:
            ctk.CTkLabel(self.scrollable_frame, text="No hay archivos para mostrar", 
                        font=("Arial", 12), text_color="gray").pack(pady=20)
            return
        
        control_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="#1E3A5F")
        control_frame.pack(fill="x", pady=(0, 5), padx=2)
        
        def seleccionar_todos():
            for var in self.archivos_data.values():
                var.set(True)
        
        def deseleccionar_todos():
            for var in self.archivos_data.values():
                var.set(False)
        
        def seleccionar_modificados():
            deseleccionar_todos()
            count = 0
            for archivo, estado in self.lista_archivos:
                if "Untracked" in estado or "Modificado" in estado or "Staged" in estado:
                    if archivo in self.archivos_data:
                        self.archivos_data[archivo].set(True)
                        count += 1
            
            if count == 0:
                messagebox.showinfo("Sin cambios", 
                    "✅ No hay archivos con cambios para añadir.\n\n"
                    "Todos los archivos están committed sin modificaciones.")
            else:
                print(f"📝 Seleccionados {count} archivos con cambios")
        
        ctk.CTkButton(control_frame, text="✓ Todos", command=seleccionar_todos, 
                     width=80, height=25, font=("Arial", 9)).pack(side="left", padx=3, pady=3)
        ctk.CTkButton(control_frame, text="✗ Ninguno", command=deseleccionar_todos, 
                     width=80, height=25, font=("Arial", 9)).pack(side="left", padx=3, pady=3)
        ctk.CTkButton(control_frame, text="📝 Solo Cambios", command=seleccionar_modificados, 
                     width=110, height=25, font=("Arial", 9), fg_color="orange").pack(side="left", padx=3, pady=3)
        
        total_archivos = len(self.lista_archivos)
        untracked = sum(1 for _, e in self.lista_archivos if "Untracked" in e)
        modificados = sum(1 for _, e in self.lista_archivos if "Modificado" in e)
        staged = sum(1 for _, e in self.lista_archivos if "Staged" in e)
        committed = sum(1 for _, e in self.lista_archivos if "Committed" in e and "Staged" not in e)
        
        info_text = f"📊 Total: {total_archivos} | 🆕 Nuevos: {untracked} | 📝 Modificados: {modificados} | ✅ Staged: {staged} | 💾 Sin cambios: {committed}"
        
        if self.archivos_ignorados_count > 0:
            info_text += f" | 🚫 Ignorados: {self.archivos_ignorados_count}"
        
        info_color = "#90EE90" if (untracked + modificados + staged) > 0 else "gray"
        
        ctk.CTkLabel(control_frame, text=info_text, font=("Arial", 9, "bold"), 
                    text_color=info_color).pack(side="right", padx=10)
        
        if self.archivos_ignorados_count > 0:
            info_ignorados = ctk.CTkFrame(self.scrollable_frame, fg_color="#3D2B1F")
            info_ignorados.pack(fill="x", pady=3, padx=2)
            
            carpetas_str = ", ".join(sorted(CARPETAS_IGNORADAS))
            ctk.CTkLabel(info_ignorados, 
                        text=f"🚫 {self.archivos_ignorados_count} archivos ignorados automáticamente de: {carpetas_str}", 
                        font=("Arial", 9), text_color="#FFA500").pack(pady=5, padx=10)
        
        if untracked == 0 and modificados == 0 and staged == 0:
            mensaje_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="#2B5B2B")
            mensaje_frame.pack(fill="x", pady=5, padx=2)
            ctk.CTkLabel(mensaje_frame, 
                        text="✅ Todos los archivos están commiteados. No hay cambios pendientes.", 
                        font=("Arial", 11, "bold"), text_color="#90EE90").pack(pady=8)
        
        header_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="#2B2B2B")
        header_frame.pack(fill="x", pady=2)
        
        ctk.CTkLabel(header_frame, text="Sel", font=("Arial", 10, "bold"), 
                    width=40, anchor="center").pack(side="left", padx=2)
        ctk.CTkLabel(header_frame, text="Archivo", font=("Arial", 11, "bold"), 
                    width=550, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="Estado Git", font=("Arial", 11, "bold"), 
                    width=200, anchor="w").pack(side="left", padx=5)
        
        for archivo, estado in self.lista_archivos:
            file_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="#1E1E1E")
            file_frame.pack(fill="x", pady=1, padx=2)
            
            var = ctk.BooleanVar()
            checkbox = ctk.CTkCheckBox(file_frame, text="", variable=var, width=40)
            checkbox.pack(side="left", padx=2)
            self.archivos_data[archivo] = var
            
            archivo_label = ctk.CTkLabel(file_frame, text=archivo, font=("Courier", 10), 
                        width=550, anchor="w")
            archivo_label.pack(side="left", padx=5)
            
            color_estado = "white"
            emoji_estado = ""
            bg_color = None
            
            if "Untracked" in estado:
                color_estado = "#FFA500"
                emoji_estado = "🆕"
                bg_color = "#3D2B1F"
            elif "Modificado" in estado:
                color_estado = "#FFFF00"
                emoji_estado = "📝"
                bg_color = "#3D3D1F"
            elif "Staged" in estado:
                color_estado = "#00FF00"
                emoji_estado = "✅"
                bg_color = "#1F3D1F"
            elif "Committed" in estado:
                color_estado = "#87CEEB"
                emoji_estado = "💾"
                bg_color = "#1F2D3D"
            else:
                emoji_estado = "📄"
            
            estado_frame = ctk.CTkFrame(file_frame, fg_color=bg_color if bg_color else "#1E1E1E", 
                                       width=200, height=25)
            estado_frame.pack(side="left", padx=5, fill="y")
            estado_frame.pack_propagate(False)
            
            estado_text = f"{emoji_estado} {estado}"
            ctk.CTkLabel(estado_frame, text=estado_text, font=("Arial", 10, "bold"), 
                        text_color=color_estado, anchor="w").pack(side="left", padx=5, fill="both", expand=True)

###################

    def _cambiar_rama_con_analisis(self, rama_destino):
        """
        Versión mejorada que verifica cambios pendientes ANTES de cambiar
        REEMPLAZA el método actual _cambiar_rama_con_analisis
        """
        if not self.proyecto or not self.proyecto.repo:
            messagebox.showwarning("Sin Git", "No hay repositorio Git inicializado.")
            return
        
        rama_origen = self.proyecto.get_rama_actual()
        
        print(f"🔀 Preparando cambio: {rama_origen} → {rama_destino}")
        
        # 1. Verificar cambios pendientes
        info_cambios = self.proyecto.verificar_cambios_pendientes()
        tiene_cambios = info_cambios['tiene_cambios']
        
        if tiene_cambios:
            print(f"⚠️ Detectados cambios pendientes:")
            for detalle in info_cambios['detalles']:
                print(f"  {detalle}")
            
            # Mostrar diálogo de opciones
            respuesta = self._mostrar_dialogo_cambios_pendientes(
                rama_origen, 
                rama_destino,
                info_cambios
            )
            
            if respuesta == "cancelar":
                print("❌ Cambio de rama cancelado por el usuario")
                return
            elif respuesta == "stash":
                # Cambiar con stash automático
                print("📦 Realizando cambio con stash automático...")
                resultado = self.proyecto.cambiar_rama_seguro(
                    rama_destino, 
                    stash_automatico=True
                )
            elif respuesta == "descartar":
                # Forzar checkout descartando cambios
                confirmacion = messagebox.askyesno(
                    "⚠️ Confirmar Descarte",
                    "⚠️ ÚLTIMA ADVERTENCIA ⚠️\n\n"
                    f"Se perderán TODOS los cambios pendientes:\n\n"
                    f"{chr(10).join(info_cambios['detalles'])}\n\n"
                    "Esta acción es IRREVERSIBLE.\n\n"
                    "¿Continuar descartando cambios?"
                )
                if not confirmacion:
                    return
                
                print("🗑️ Descartando cambios y cambiando de rama...")
                resultado = self.proyecto.cambiar_rama_seguro(
                    rama_destino,
                    forzar=True
                )
            elif respuesta == "commit":
                # Abrir ventana de commit
                messagebox.showinfo("Commit Primero", 
                    "Realiza el commit de tus cambios y luego intenta cambiar de rama nuevamente.")
                self.git_commit()
                return
        else:
            # No hay cambios, cambio directo
            print("✅ No hay cambios pendientes, procediendo con checkout...")
            resultado = self.proyecto.cambiar_rama_seguro(rama_destino)
        
        # 2. Procesar resultado del cambio
        if resultado['exito']:
            print(f"✅ Checkout exitoso a {rama_destino}")
            
            # 3. Actualizar UI
            self.actualizar_rama_display()
            self.ver_archivos()
            
            # 4. Detectar divergencias DESPUÉS del cambio exitoso
            print(f"🔍 Analizando divergencias entre ramas...")
            divergencias = self.proyecto.detectar_divergencia_ramas(rama_origen, rama_destino)
            
            # 5. Construir mensaje de éxito
            mensaje_exito = f"✅ Cambiado a la rama '{rama_destino}'\n\n"
            mensaje_exito += "📂 Directorio de trabajo actualizado.\n"
            
            if resultado.get('stash_aplicado'):
                mensaje_exito += "\n📦 Tus cambios están guardados en stash."
                mensaje_exito += "\n💡 Usa 'Gestionar Stashes' para recuperarlos cuando quieras."
            
            # 6. Mostrar análisis de divergencias si existen
            if divergencias:
                mensaje_exito += f"\n\n⚠️ Se detectaron {len(divergencias)} archivo(s) con versiones diferentes entre ramas."
                
                messagebox.showinfo("Cambio Exitoso", mensaje_exito)
                
                # Mostrar ventana de divergencias
                self._mostrar_analisis_divergencias(rama_origen, rama_destino, divergencias)
            else:
                mensaje_exito += "\n✨ No se detectaron divergencias entre ramas."
                messagebox.showinfo("Cambio Exitoso", mensaje_exito)
        else:
            # Error en el cambio
            if resultado.get('requiere_stash'):
                # Este caso ya fue manejado arriba, no debería llegar aquí
                print("⚠️ Requiere stash (caso ya manejado)")
            else:
                error_msg = resultado.get('mensaje', 'Error desconocido')
                messagebox.showerror("Error al Cambiar Rama", 
                    f"❌ No se pudo cambiar a la rama '{rama_destino}':\n\n{error_msg}")

    def _mostrar_dialogo_cambios_pendientes(self, rama_origen, rama_destino, info_cambios):
        """
        Muestra diálogo modal para decidir qué hacer con cambios pendientes
        
        Returns:
            str: "stash", "commit", "descartar" o "cancelar"
        """
        ventana = ctk.CTkToplevel(self.root)
        ventana.title("⚠️ Cambios Pendientes")
        ventana.geometry("600x550")
        ventana.transient(self.root)
        ventana.grab_set()
        ventana.attributes('-topmost', True)
        
        # Centrar ventana
        ventana.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (600 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (550 // 2)
        ventana.geometry(f"+{x}+{y}")
        
        resultado = {"accion": "cancelar"}
        
        # Header con advertencia
        header_frame = ctk.CTkFrame(ventana, fg_color="#3D2B1F")
        header_frame.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(header_frame, 
                    text="⚠️ Tienes cambios sin guardar",
                    font=("Arial", 18, "bold"),
                    text_color="orange").pack(pady=10)
        
        ctk.CTkLabel(header_frame,
                    text=f"Cambio solicitado: {rama_origen} → {rama_destino}",
                    font=("Arial", 11),
                    text_color="#FFD700").pack(pady=5)
        
        # Información de cambios
        info_frame = ctk.CTkFrame(ventana, fg_color="#2B2B2B")
        info_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(info_frame,
                    text="📋 Cambios detectados:",
                    font=("Arial", 11, "bold")).pack(pady=5, anchor="w", padx=10)
        
        for detalle in info_cambios['detalles']:
            ctk.CTkLabel(info_frame,
                        text=f"  • {detalle}",
                        font=("Arial", 10),
                        text_color="#87CEEB",
                        anchor="w").pack(pady=2, padx=20, anchor="w")
        
        # Instrucciones
        ctk.CTkLabel(ventana,
                    text="¿Qué deseas hacer con estos cambios?",
                    font=("Arial", 12, "bold")).pack(pady=15)
        
        # Frame de opciones
        opciones_frame = ctk.CTkFrame(ventana, fg_color="transparent")
        opciones_frame.pack(fill="both", expand=True, padx=20, pady=5)
        
        def seleccionar(accion):
            resultado["accion"] = accion
            ventana.destroy()
        
        # Opción 1: Stash (RECOMENDADA)
        btn_stash = ctk.CTkButton(
            opciones_frame,
            text="📦 Guardar Temporalmente (Stash)\n\n"
                "✅ Recomendado • Seguro • Reversible\n"
                "Los cambios se guardan y puedes recuperarlos después",
            command=lambda: seleccionar("stash"),
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            height=75,
            font=("Arial", 11, "bold"),
            corner_radius=8
        )
        btn_stash.pack(fill="x", pady=5)
        
        # Opción 2: Commit
        btn_commit = ctk.CTkButton(
            opciones_frame,
            text="💾 Hacer Commit Ahora\n\n"
                "Guarda los cambios permanentemente antes de cambiar",
            command=lambda: seleccionar("commit"),
            fg_color="#1976D2",
            hover_color="#0D47A1",
            height=65,
            font=("Arial", 11),
            corner_radius=8
        )
        btn_commit.pack(fill="x", pady=5)
        
        # Opción 3: Descartar (PELIGROSO)
        btn_descartar = ctk.CTkButton(
            opciones_frame,
            text="🗑️ Descartar Cambios\n\n"
                "⚠️ PELIGRO: Elimina todos los cambios sin guardar",
            command=lambda: seleccionar("descartar"),
            fg_color="#D32F2F",
            hover_color="#B71C1C",
            height=65,
            font=("Arial", 11),
            corner_radius=8
        )
        btn_descartar.pack(fill="x", pady=5)
        
        # Opción 4: Cancelar
        btn_cancelar = ctk.CTkButton(
            opciones_frame,
            text="❌ Cancelar - No cambiar de rama",
            command=lambda: seleccionar("cancelar"),
            fg_color="#616161",
            hover_color="#424242",
            height=45,
            font=("Arial", 10),
            corner_radius=8
        )
        btn_cancelar.pack(fill="x", pady=5)
        
        # Nota al pie
        nota_frame = ctk.CTkFrame(ventana, fg_color="#1E3A5F")
        nota_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        ctk.CTkLabel(nota_frame,
                    text="💡 Tip: Si no estás seguro, elige 'Guardar Temporalmente'",
                    font=("Arial", 9),
                    text_color="#90EE90").pack(pady=5)
        
        # Esperar respuesta
        ventana.wait_window()
        return resultado["accion"]

    def gestionar_stashes(self):
        """
        Ventana para visualizar y gestionar stashes guardados
        NUEVO MÉTODO - Agregar botón en UI
        """
        if not self.proyecto or not self.proyecto.repo:
            messagebox.showwarning("Sin Git", "No hay repositorio Git inicializado.")
            return
        
        stashes = self.proyecto.listar_stashes()
        
        if not stashes:
            messagebox.showinfo("Sin Stashes", 
                "📦 No hay stashes guardados.\n\n"
                "Los stashes se crean automáticamente cuando:\n"
                "• Cambias de rama con cambios pendientes\n"
                "• Usas la opción 'Guardar Temporalmente'")
            return
        
        ventana = ctk.CTkToplevel(self.root)
        ventana.title("📦 Gestionar Stashes")
        ventana.geometry("750x550")
        ventana.transient(self.root)
        ventana.grab_set()
        ventana.attributes('-topmost', True)
        
        # Header
        ctk.CTkLabel(ventana, 
                    text="📦 Stashes Guardados",
                    font=("Arial", 18, "bold")).pack(pady=15)
        
        rama_actual = self.proyecto.get_rama_actual()
        ctk.CTkLabel(ventana,
                    text=f"🌿 Rama actual: {rama_actual}",
                    font=("Arial", 11),
                    text_color="#90EE90").pack(pady=5)
        
        # Info
        info_frame = ctk.CTkFrame(ventana, fg_color="#2B2B2B")
        info_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(info_frame,
                    text=f"Total de stashes: {len(stashes)}",
                    font=("Arial", 11)).pack(side="left", padx=10, pady=8)
        
        ctk.CTkLabel(info_frame,
                    text="💡 Los stashes se aplican en la rama actual",
                    font=("Arial", 9),
                    text_color="#87CEEB").pack(side="right", padx=10)
        
        # Lista de stashes
        scroll_frame = ctk.CTkScrollableFrame(ventana, width=700, height=280)
        scroll_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        stash_seleccionado = {"index": None, "data": None}
        
        for stash in stashes:
            stash_frame = ctk.CTkFrame(scroll_frame, fg_color="#1E1E1E")
            stash_frame.pack(fill="x", pady=3, padx=5)
            
            # Radio button
            radio = ctk.CTkRadioButton(
                stash_frame, 
                text="",
                value=stash['index'],
                command=lambda idx=stash['index'], data=stash: stash_seleccionado.update({
                    "index": idx,
                    "data": data
                })
            )
            radio.pack(side="left", padx=5)
            
            # Info del stash
            info_stash = ctk.CTkFrame(stash_frame, fg_color="transparent")
            info_stash.pack(side="left", fill="x", expand=True, padx=10)
            
            ctk.CTkLabel(info_stash,
                        text=f"📦 {stash['ref']} - {stash['tipo']}",
                        font=("Courier", 9, "bold"),
                        anchor="w").pack(anchor="w")
            
            ctk.CTkLabel(info_stash,
                        text=stash['mensaje'],
                        font=("Arial", 9),
                        anchor="w",
                        text_color="#87CEEB").pack(anchor="w")
        
        # Botones de acción
        button_frame = ctk.CTkFrame(ventana, fg_color="transparent")
        button_frame.pack(pady=15)
        
        def aplicar_stash():
            if stash_seleccionado["index"] is None:
                messagebox.showwarning("Sin Selección", "Selecciona un stash para aplicar.")
                return
            
            idx = stash_seleccionado["index"]
            data = stash_seleccionado["data"]
            
            respuesta = messagebox.askyesno(
                "Aplicar Stash",
                f"¿Aplicar el stash seleccionado?\n\n"
                f"📦 {data['ref']}\n"
                f"📝 {data['mensaje']}\n\n"
                f"Los cambios se aplicarán en la rama actual: {rama_actual}\n\n"
                "El stash se eliminará después de aplicarse."
            )
            
            if not respuesta:
                return
            
            resultado = self.proyecto.aplicar_stash(idx, eliminar_despues=True)
            
            if resultado == True:
                messagebox.showinfo("Éxito", 
                    "✅ Stash aplicado correctamente.\n\n"
                    "Los cambios ahora están en tu directorio de trabajo.")
                ventana.destroy()
                self.ver_archivos()
            else:
                messagebox.showerror("Error", f"Error al aplicar stash:\n\n{resultado}")
        
        def eliminar_stash():
            if stash_seleccionado["index"] is None:
                messagebox.showwarning("Sin Selección", "Selecciona un stash para eliminar.")
                return
            
            idx = stash_seleccionado["index"]
            data = stash_seleccionado["data"]
            
            respuesta = messagebox.askyesno(
                "⚠️ Eliminar Stash",
                f"¿Eliminar el stash seleccionado?\n\n"
                f"📦 {data['ref']}\n"
                f"📝 {data['mensaje']}\n\n"
                "⚠️ Esta acción no se puede deshacer."
            )
            
            if not respuesta:
                return
            
            resultado = self.proyecto.eliminar_stash(idx)
            
            if resultado == True:
                messagebox.showinfo("Eliminado", "🗑️ Stash eliminado correctamente.")
                ventana.destroy()
                if len(stashes) > 1:
                    self.gestionar_stashes()  # Reabrir si quedan más
            else:
                messagebox.showerror("Error", f"Error al eliminar stash:\n\n{resultado}")
        
        ctk.CTkButton(
            button_frame,
            text="✅ Aplicar Stash",
            command=aplicar_stash,
            fg_color="#2E7D32",
            width=150,
            height=40,
            font=("Arial", 11, "bold")
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="🗑️ Eliminar",
            command=eliminar_stash,
            fg_color="#D32F2F",
            width=120,
            height=40
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="❌ Cerrar",
            command=ventana.destroy,
            fg_color="gray",
            width=120,
            height=40
        ).pack(side="left", padx=5)

###################

    # ==================== GIT OPERATIONS ====================

    def git_add(self):
        if not self.proyecto or not self.proyecto.repo:
            messagebox.showwarning("Sin Git", "No hay repositorio Git inicializado.")
            return
            
        archivos_seleccionados = []
        estados_seleccionados = {}
        
        for archivo, var in self.archivos_data.items():
            if var.get():
                archivos_seleccionados.append(archivo)
                for arch, estado in self.lista_archivos:
                    if arch == archivo:
                        estados_seleccionados[archivo] = estado
                        break

        if not archivos_seleccionados:
            messagebox.showinfo("Sin selección", "Seleccioná al menos un archivo para añadir.")
            return

        archivos_sin_cambios = []
        archivos_con_cambios = []
        
        for archivo in archivos_seleccionados:
            estado = estados_seleccionados.get(archivo, "")
            if "Committed" in estado and "Staged" not in estado:
                archivos_sin_cambios.append(archivo)
            else:
                archivos_con_cambios.append(archivo)
        
        if len(archivos_sin_cambios) == len(archivos_seleccionados):
            messagebox.showinfo("Sin cambios para añadir", 
                f"⚠️ Los archivos seleccionados no tienen cambios.\n\n"
                f"Git solo añade al staging area archivos que tienen:\n"
                f"• Modificaciones (📝)\n"
                f"• Son nuevos (🆕)\n\n"
                f"Archivos seleccionados:\n" + "\n".join([f"  • {a}" for a in archivos_sin_cambios[:5]]) +
                ("\n  ..." if len(archivos_sin_cambios) > 5 else ""))
            return
        
        if archivos_sin_cambios:
            respuesta = messagebox.askyesno("Archivos sin cambios detectados",
                f"⚠️ {len(archivos_sin_cambios)} archivo(s) no tienen cambios y serán ignorados.\n\n"
                f"Archivos sin cambios:\n" + "\n".join([f"  • {a}" for a in archivos_sin_cambios[:3]]) +
                ("\n  ..." if len(archivos_sin_cambios) > 3 else "") +
                f"\n\n¿Continuar añadiendo los {len(archivos_con_cambios)} archivo(s) con cambios?")
            if not respuesta:
                return
            
            archivos_seleccionados = archivos_con_cambios

        print(f"📤 Añadiendo {len(archivos_seleccionados)} archivo(s) al stage...")
        for archivo in archivos_seleccionados:
            estado = estados_seleccionados.get(archivo, "")
            print(f"  → {archivo} [{estado}]")
        
        resultado = self.proyecto.git_add(archivos_seleccionados)
        if resultado == True:
            ventana_exito = ctk.CTkToplevel(self.root)
            ventana_exito.title("✅ Git Add Exitoso")
            ventana_exito.geometry("500x450")
            ventana_exito.transient(self.root)
            ventana_exito.attributes('-topmost', True)
            ventana_exito.grab_set()
            
            ctk.CTkLabel(ventana_exito, text="✅ Archivos añadidos al Stage", 
                        font=("Arial", 14, "bold"), text_color="green").pack(pady=15)
            
            ctk.CTkLabel(ventana_exito, text=f"Total: {len(archivos_seleccionados)} archivo(s)", 
                        font=("Arial", 12)).pack(pady=5)
            
            if archivos_sin_cambios:
                ctk.CTkLabel(ventana_exito, 
                            text=f"⚠️ {len(archivos_sin_cambios)} archivo(s) sin cambios (ignorados)", 
                            font=("Arial", 10), text_color="orange").pack(pady=3)
            
            scroll_frame = ctk.CTkScrollableFrame(ventana_exito, width=450, height=120)
            scroll_frame.pack(pady=10, padx=20)
            
            for archivo in archivos_seleccionados:
                ctk.CTkLabel(scroll_frame, text=f"✓ {archivo}", 
                            font=("Courier", 9), anchor="w", 
                            text_color="#90EE90").pack(anchor="w", pady=1)
            
            if archivos_sin_cambios:
                ctk.CTkLabel(ventana_exito, text="Archivos sin cambios (no añadidos):", 
                            font=("Arial", 9, "bold")).pack(pady=(10, 3))
                scroll_frame2 = ctk.CTkScrollableFrame(ventana_exito, width=450, height=60)
                scroll_frame2.pack(pady=3, padx=20)
                
                for archivo in archivos_sin_cambios:
                    ctk.CTkLabel(scroll_frame2, text=f"○ {archivo}", 
                                font=("Courier", 8), anchor="w", 
                                text_color="gray").pack(anchor="w", pady=1)
            
            ctk.CTkLabel(ventana_exito, 
                        text="Los archivos ahora están en el staging area.\n¿Querés hacer commit ahora?", 
                        font=("Arial", 10)).pack(pady=10)
            
            def hacer_commit_ahora():
                ventana_exito.destroy()
                self.git_commit()
            
            button_frame = ctk.CTkFrame(ventana_exito, fg_color="transparent")
            button_frame.pack(pady=10)
            
            ctk.CTkButton(button_frame, text="✅ Sí, Commit Ahora", 
                         command=hacer_commit_ahora,
                         fg_color="green", hover_color="darkgreen", 
                         width=150).pack(side="left", padx=5)
            
            ctk.CTkButton(button_frame, text="❌ No, Después", 
                         command=ventana_exito.destroy,
                         fg_color="gray", width=150).pack(side="left", padx=5)
            
            self.root.after(500, self.ver_archivos)
        else:
            messagebox.showerror("Error Git Add", f"Error al añadir archivos:\n{resultado}")

    def git_commit(self):
        if not self.proyecto or not self.proyecto.repo:
            messagebox.showwarning("Sin Git", "No hay repositorio Git inicializado.")
            return
        
        git_estado = self.proyecto.estado_archivos()
        archivos_staged = git_estado.get("staged", [])
        
        if not archivos_staged:
            respuesta = messagebox.askyesno("Sin archivos en stage",
                "No hay archivos en el staging area.\n\n"
                "¿Querés añadir archivos primero con 'Git Add'?")
            if respuesta:
                return
            else:
                return
        
        ventana_commit = ctk.CTkToplevel(self.root)
        ventana_commit.title("✅ Git Commit")
        ventana_commit.geometry("600x600")
        ventana_commit.transient(self.root)
        ventana_commit.attributes('-topmost', True)
        ventana_commit.grab_set()
        
        ctk.CTkLabel(ventana_commit, text="💾 Crear Commit", 
                    font=("Arial", 16, "bold")).pack(pady=15)
        
        ctk.CTkLabel(ventana_commit, 
                    text=f"📊 Archivos en staging area: {len(archivos_staged)}", 
                    font=("Arial", 12, "bold"), text_color="#90EE90").pack(pady=5)
        
        scroll_frame = ctk.CTkScrollableFrame(ventana_commit, width=550, height=80)
        scroll_frame.pack(pady=10, padx=20)
        
        for archivo in archivos_staged:
            ctk.CTkLabel(scroll_frame, text=f"✓ {archivo}", 
                        font=("Courier", 9), anchor="w", 
                        text_color="#87CEEB").pack(anchor="w", pady=1)
        
        ctk.CTkLabel(ventana_commit, text="📝 Mensaje del commit:", 
                    font=("Arial", 12, "bold")).pack(pady=(10, 5))
        
        mensaje_textbox = ctk.CTkTextbox(ventana_commit, height=80, width=550, 
                                         font=("Arial", 11))
        mensaje_textbox.pack(pady=5, padx=20)
        mensaje_textbox.insert("1.0", "Update files")
        
        sugerencias_frame = ctk.CTkFrame(ventana_commit, fg_color="transparent")
        sugerencias_frame.pack(pady=5)
        
        ctk.CTkLabel(sugerencias_frame, text="💡 Sugerencias:", 
                    font=("Arial", 9)).pack(side="left", padx=5)
        
        def usar_sugerencia(texto):
            mensaje_textbox.delete("1.0", "end")
            mensaje_textbox.insert("1.0", texto)
        
        sugerencias = [
            "feat: nueva funcionalidad",
            "fix: corrección de bug",
            "docs: actualización de documentación"
        ]
        
        for sug in sugerencias:
            ctk.CTkButton(sugerencias_frame, text=sug, 
                         command=lambda s=sug: usar_sugerencia(s),
                         width=160, height=20, font=("Arial", 8),
                         fg_color="#3D3D3D").pack(side="left", padx=2)
        
        button_frame = ctk.CTkFrame(ventana_commit, fg_color="transparent")
        button_frame.pack(pady=20)
        
        def realizar_commit():
            mensaje = mensaje_textbox.get("1.0", "end").strip()
            
            if not mensaje:
                messagebox.showwarning("Mensaje vacío", "Debes escribir un mensaje de commit.")
                return
            
            print(f"💾 Realizando commit: {mensaje}")
            ventana_commit.destroy()
            
            ventana_progreso = self._crear_ventana_progreso(
                "💾 Creando commit...",
                "Procesando el commit..."
            )
            
            def commit_thread():
                resultado = self.proyecto.git_commit(mensaje)
                self.root.after(0, lambda: self._procesar_commit(resultado, ventana_progreso, mensaje, archivos_staged))
            
            threading.Thread(target=commit_thread, daemon=True).start()
        
        ctk.CTkButton(button_frame, text="✅ Crear Commit", 
                     command=realizar_commit,
                     fg_color="green", hover_color="darkgreen", 
                     width=180, height=40, font=("Arial", 12, "bold")).pack(side="left", padx=5)
        
        ctk.CTkButton(button_frame, text="❌ Cancelar", 
                     command=ventana_commit.destroy,
                     fg_color="red", hover_color="darkred", 
                     width=120, height=40).pack(side="left", padx=5)

    def _procesar_commit(self, resultado, ventana_progreso, mensaje, archivos_staged):
        ventana_progreso.destroy()
        
        if resultado == True:
            ventana_exito = ctk.CTkToplevel(self.root)
            ventana_exito.title("✅ Commit Exitoso")
            ventana_exito.geometry("500x350")
            ventana_exito.transient(self.root)
            ventana_exito.attributes('-topmost', True)
            ventana_exito.grab_set()
            
            ctk.CTkLabel(ventana_exito, text="✅ Commit Realizado Exitosamente", 
                        font=("Arial", 14, "bold"), text_color="green").pack(pady=20)
            
            ctk.CTkLabel(ventana_exito, text=f"📝 {mensaje}", 
                        font=("Arial", 11), wraplength=450).pack(pady=10)
            
            ctk.CTkLabel(ventana_exito, text=f"📊 Archivos commiteados: {len(archivos_staged)}", 
                        font=("Arial", 10)).pack(pady=5)
            
            try:
                ultimo_commit = list(self.proyecto.repo.iter_commits(max_count=1))[0]
                commit_hash = ultimo_commit.hexsha[:8]
                ctk.CTkLabel(ventana_exito, text=f"🔹 Hash: {commit_hash}", 
                            font=("Courier", 10), text_color="#87CEEB").pack(pady=5)
            except:
                pass
            
            ctk.CTkLabel(ventana_exito, text="¿Querés hacer push al repositorio remoto?", 
                        font=("Arial", 10)).pack(pady=10)
            
            def hacer_push():
                ventana_exito.destroy()
                self.push()
            
            btn_frame = ctk.CTkFrame(ventana_exito, fg_color="transparent")
            btn_frame.pack(pady=10)
            
            ctk.CTkButton(btn_frame, text="⬆️ Sí, Push Ahora", 
                         command=hacer_push,
                         fg_color="blue", hover_color="darkblue", 
                         width=140).pack(side="left", padx=5)
            
            ctk.CTkButton(btn_frame, text="❌ No, Después", 
                         command=ventana_exito.destroy,
                         fg_color="gray", width=140).pack(side="left", padx=5)
            
            self.actualizar_rama_display()
            self.ver_archivos()
        else:
            messagebox.showerror("Error Git Commit", f"Error al hacer commit:\n{resultado}")

    def push(self):
        if not self.proyecto or not self.proyecto.repo:
            messagebox.showwarning("Sin Git", "No hay repositorio Git inicializado.")
            return
            
        print("⬆️ Haciendo push...")
        resultado = self.proyecto.push()
        if resultado == True:
            messagebox.showinfo("Push exitoso", "✅ Push realizado correctamente.")
        else:
            messagebox.showerror("Error Push", f"Error al hacer push:\n{resultado}")

    def pull(self):
        if not self.proyecto or not self.proyecto.repo:
            messagebox.showwarning("Sin Git", "No hay repositorio Git inicializado.")
            return
            
        print("⬇️ Haciendo pull...")
        resultado = self.proyecto.pull()
        if resultado == True:
            messagebox.showinfo("Pull exitoso", "✅ Pull realizado correctamente.")
            self.actualizar_rama_display()
            self.ver_archivos()
        else:
            messagebox.showerror("Error Pull", f"Error al hacer pull:\n{resultado}")

    def ver_log(self):
        if not self.proyecto or not self.proyecto.repo:
            messagebox.showwarning("Sin Git", "No hay repositorio Git inicializado.")
            return
            
        log = self.proyecto.get_git_log(10)
        if isinstance(log, str) and not log.startswith("error"):
            ventana_log = ctk.CTkToplevel(self.root)
            ventana_log.title("📜 Log de Commits")
            ventana_log.geometry("700x400")
            ventana_log.attributes('-topmost', True)
            
            text_widget = ctk.CTkTextbox(ventana_log, font=("Courier", 10))
            text_widget.pack(fill="both", expand=True, padx=10, pady=10)
            text_widget.insert("1.0", log)
            text_widget.configure(state="disabled")
        else:
            messagebox.showerror("Error", f"Error al obtener log:\n{log}")

    def ver_status(self):
        if not self.proyecto or not self.proyecto.repo:
            messagebox.showwarning("Sin Git", "No hay repositorio Git inicializado.")
            return
            
        status = self.proyecto.get_git_status()
        if isinstance(status, str) and not status.startswith("error"):
            ventana_status = ctk.CTkToplevel(self.root)
            ventana_status.title("🔍 Status del Repositorio")
            ventana_status.geometry("600x300")
            ventana_status.attributes('-topmost', True)
            
            text_widget = ctk.CTkTextbox(ventana_status, font=("Courier", 9))
            text_widget.pack(fill="both", expand=True, padx=10, pady=10)
            text_widget.insert("1.0", status)
            text_widget.configure(state="disabled")
        else:
            messagebox.showerror("Error", f"Error al obtener status:\n{status}")

    # ==================== RAMAS Y REMOTOS ====================

    def nueva_rama(self):
        if not self.proyecto or not self.proyecto.repo:
            messagebox.showwarning("Sin Git", "No hay repositorio Git inicializado.")
            return
            
        dialog = CTkInputDialog(
            parent=self.root,
            title="🧪 Nueva Rama",
            prompt="Nombre de la nueva rama experimental:",
            initialvalue="feature/nueva-funcionalidad"
        )
        
        nombre = dialog.result
        if nombre:
            print(f"🧪 Creando rama: {nombre}")
            resultado = self.proyecto.crear_rama(nombre)
            if resultado == True:
                self.actualizar_rama_display()
                messagebox.showinfo("Rama creada", f"✅ Rama '{nombre}' creada y activa.")
                self.ver_archivos()
            else:
                messagebox.showerror("Error", f"Error al crear rama:\n{resultado}")

    def cambiar_rama(self):
        if not self.proyecto or not self.proyecto.repo:
            messagebox.showwarning("Sin Git", "No hay repositorio Git inicializado.")
            return
        
        ramas_info = self.proyecto.listar_ramas()
        ramas_locales = ramas_info.get('locales', [])
        
        if not ramas_locales:
            messagebox.showinfo("Sin ramas", "No hay ramas disponibles.")
            return
        
        ventana_ramas = ctk.CTkToplevel(self.root)
        ventana_ramas.title("🔀 Cambiar Rama")
        ventana_ramas.geometry("500x500")
        ventana_ramas.transient(self.root)
        ventana_ramas.attributes('-topmost', True)
        ventana_ramas.grab_set()
        
        ctk.CTkLabel(ventana_ramas, text="🔀 Seleccionar Rama", 
                    font=("Arial", 16, "bold")).pack(pady=15)
        
        rama_actual = self.proyecto.get_rama_actual()
        ctk.CTkLabel(ventana_ramas, text=f"📍 Rama actual: {rama_actual}", 
                    font=("Arial", 12), text_color="#90EE90").pack(pady=5)
        
        # ⭐ NUEVO: Frame de advertencia sobre divergencias
        warning_frame = ctk.CTkFrame(ventana_ramas, fg_color="#3D2B1F")
        warning_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(warning_frame, 
                    text="ℹ️ Al cambiar de rama, se analizarán divergencias automáticamente", 
                    font=("Arial", 9), text_color="orange").pack(pady=5)


        ctk.CTkLabel(ventana_ramas, text="Seleccioná la rama destino:", 
                    font=("Arial", 11)).pack(pady=10)
        
        scroll_frame = ctk.CTkScrollableFrame(ventana_ramas, width=450, height=200)
        scroll_frame.pack(pady=10, padx=20)
        
        rama_seleccionada = {"nombre": None}
        
        def seleccionar_rama(rama):
            rama_seleccionada["nombre"] = rama
        
        for rama in ramas_locales:
            rama_frame = ctk.CTkFrame(scroll_frame, fg_color="#1E1E1E")
            rama_frame.pack(fill="x", pady=2)
            
            es_actual = (rama == rama_actual)
            color_bg = "#2E7D32" if es_actual else "#1E1E1E"
            
            radio = ctk.CTkRadioButton(rama_frame, text="", value=rama,
                                       command=lambda r=rama: seleccionar_rama(r))
            radio.pack(side="left", padx=5)
            
            icono = "📍" if es_actual else "🌿"
            ctk.CTkLabel(rama_frame, text=f"{icono} {rama}", 
                        font=("Arial", 11, "bold" if es_actual else "normal"),
                        text_color="#90EE90" if es_actual else "white").pack(side="left", padx=10)
        
        def confirmar_cambio():
            if not rama_seleccionada["nombre"]:
                messagebox.showwarning("Sin selección", "Seleccioná una rama.")
                return
            
            if rama_seleccionada["nombre"] == rama_actual:
                messagebox.showinfo("Misma rama", "Ya estás en esa rama.")
                return
            
            ventana_ramas.destroy()
            
            # ⭐ NUEVO: Analizar divergencias ANTES de cambiar
            self._cambiar_rama_con_analisis(rama_seleccionada['nombre'])
        
        button_frame = ctk.CTkFrame(ventana_ramas, fg_color="transparent")
        button_frame.pack(pady=15)
        
        ctk.CTkButton(button_frame, text="✅ Cambiar", command=confirmar_cambio,
                    fg_color="green", width=120, height=35,
                    font=("Arial", 11, "bold")).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="❌ Cancelar", command=ventana_ramas.destroy,
                    fg_color="gray", width=120, height=35).pack(side="left", padx=5)

    def _cambiar_rama_con_analisis(self, rama_destino):
        """Cambia de rama y analiza divergencias automáticamente"""
        rama_origen = self.proyecto.get_rama_actual()
        
        print(f"🔀 Cambiando de {rama_origen} → {rama_destino}")
        print(f"🔍 Analizando divergencias entre ramas...")
        
        # Detectar divergencias ANTES de cambiar
        divergencias = self.proyecto.detectar_divergencia_ramas(rama_origen, rama_destino)
        
        # Cambiar de rama
        resultado = self.proyecto.cambiar_rama(rama_destino)
        
        if resultado == True:
            self.actualizar_rama_display()
            self.ver_archivos()
            
            # Si hay divergencias, mostrar análisis
            if divergencias:
                self._mostrar_analisis_divergencias(rama_origen, rama_destino, divergencias)
            else:
                messagebox.showinfo("Cambio exitoso", 
                    f"✅ Cambiado a la rama '{rama_destino}'.\n\n"
                    "✨ No se detectaron divergencias entre ramas.")
        else:
            messagebox.showerror("Error", f"Error al cambiar de rama:\n{resultado}")

    def _mostrar_analisis_divergencias(self, rama_origen, rama_destino, divergencias):
        """Muestra ventana con análisis detallado de divergencias"""
        ventana_div = ctk.CTkToplevel(self.root)
        ventana_div.title("⚠️ Divergencia Detectada")
        ventana_div.geometry("1000x600")
        ventana_div.transient(self.root)
        ventana_div.attributes('-topmost', True)
        ventana_div.grab_set()
        
        ctk.CTkLabel(ventana_div, text="⚠️ Divergencia entre Ramas Detectada", 
                    font=("Arial", 16, "bold"), text_color="orange").pack(pady=15)
        
        # Info de ramas
        info_frame = ctk.CTkFrame(ventana_div, fg_color="#3D2B1F")
        info_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(info_frame, 
                    text=f"Se detectaron {len(divergencias)} archivo(s) con commits diferentes\n"
                        f"entre '{rama_origen}' y '{rama_destino}'", 
                    font=("Arial", 11), text_color="orange").pack(pady=8)
        
        # Explicación
        explicacion = ctk.CTkFrame(ventana_div, fg_color="#2B2B2B")
        explicacion.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(explicacion, 
                    text="ℹ️ Divergencia significa que estos archivos tienen versiones diferentes en cada rama.\n"
                        "Esto ocurre cuando se hacen commits en ambas ramas de forma independiente.", 
                    font=("Arial", 9), text_color="#87CEEB", 
                    justify="left").pack(pady=8, padx=10)
        
        # Lista de divergencias
        ctk.CTkLabel(ventana_div, text="Archivos divergentes:", 
                    font=("Arial", 12, "bold")).pack(pady=10)
        
        scroll_frame = ctk.CTkScrollableFrame(ventana_div, width=950, height=250)
        scroll_frame.pack(pady=5, padx=20)
        
        # Header
        header = ctk.CTkFrame(scroll_frame, fg_color="#1E3A5F")
        header.pack(fill="x", pady=2)
        ctk.CTkLabel(header, text="Archivo", font=("Arial", 10, "bold"), width=250).pack(side="left", padx=5)
        ctk.CTkLabel(header, text=f"{rama_origen}", font=("Arial", 10, "bold"), width=200).pack(side="left", padx=5)
        ctk.CTkLabel(header, text=f"{rama_destino}", font=("Arial", 10, "bold"), width=200).pack(side="left", padx=5)
        ctk.CTkLabel(header, text="Más reciente", font=("Arial", 10, "bold"), width=150).pack(side="left", padx=5)
        
        for archivo, info in divergencias.items():
            archivo_frame = ctk.CTkFrame(scroll_frame, fg_color="#1E1E1E")
            archivo_frame.pack(fill="x", pady=2, padx=5)
            
            # Nombre del archivo
            archivo_corto = archivo if len(archivo) < 35 else "..." + archivo[-32:]
            ctk.CTkLabel(archivo_frame, text=f"📄 {archivo_corto}", 
                        font=("Arial", 9), width=250, anchor="w").pack(side="left", padx=5)
            
            # Info rama origen
            info_origen = info.get(rama_origen, {})
            fecha_origen = info_origen.get('fecha', 'N/A')
            hash_origen = info_origen.get('hash', 'N/A')
            ctk.CTkLabel(archivo_frame, text=f"{hash_origen} | {fecha_origen}", 
                        font=("Courier", 8), width=200).pack(side="left", padx=5)
            
            # Info rama destino
            info_destino = info.get(rama_destino, {})
            fecha_destino = info_destino.get('fecha', 'N/A')
            hash_destino = info_destino.get('hash', 'N/A')
            ctk.CTkLabel(archivo_frame, text=f"{hash_destino} | {fecha_destino}", 
                        font=("Courier", 8), width=200).pack(side="left", padx=5)
            
            # Indicador de cuál es más reciente
            mas_reciente = info.get('mas_reciente', 'N/A')
            color = "#90EE90" if mas_reciente == rama_destino else "#FFB74D"
            ctk.CTkLabel(archivo_frame, text=f"🕐 {mas_reciente}", 
                        font=("Arial", 9, "bold"), width=150,
                        text_color=color).pack(side="left", padx=5)
            
            # Botón comparar
            def comparar_archivo(arch=archivo, info_arch=info):
                self._comparar_archivo_entre_ramas(arch, rama_origen, rama_destino, info_arch)
            
            ctk.CTkButton(archivo_frame, text="🔍", command=comparar_archivo,
                        width=30, height=25, fg_color="#1E90FF",
                        font=("Arial", 10)).pack(side="left", padx=5)
        
        # Análisis de merge
        analisis_merge = self.proyecto.analizar_merge_previo(rama_origen)
        
        if analisis_merge:
            merge_info_frame = ctk.CTkFrame(ventana_div, fg_color="#1E3A5F")
            merge_info_frame.pack(fill="x", padx=20, pady=10)
            
            if analisis_merge['requiere_merge']:
                texto = f"⚠️ Se requiere MERGE para sincronizar:\n"
                texto += f"• '{rama_destino}' tiene {analisis_merge['commits_adelante']} commit(s) adelante\n"
                texto += f"• '{rama_origen}' tiene {analisis_merge['commits_atras']} commit(s) que no están en '{rama_destino}'"
                color = "orange"
            else:
                texto = f"✅ Merge sería FAST-FORWARD (sin conflictos esperados)\n"
                texto += f"• '{rama_destino}' tiene {analisis_merge['commits_adelante']} commit(s) adelante"
                color = "#90EE90"
            
            ctk.CTkLabel(merge_info_frame, text=texto, 
                        font=("Arial", 10), text_color=color,
                        justify="left").pack(pady=8, padx=10)
        
        # Botones de acción
        button_frame = ctk.CTkFrame(ventana_div, fg_color="transparent")
        button_frame.pack(pady=15)
        
        def fusionar_ramas():
            ventana_div.destroy()
            respuesta = messagebox.askyesno("Confirmar Merge",
                f"¿Fusionar '{rama_origen}' en '{rama_destino}'?\n\n"
                f"Esto integrará los cambios de '{rama_origen}' en tu rama actual '{rama_destino}'.")
            
            if respuesta:
                self._ejecutar_merge(rama_origen)
        
        ctk.CTkButton(button_frame, text="🔀 Fusionar Ramas (Merge)", 
                    command=fusionar_ramas,
                    fg_color="#7B1FA2", hover_color="#6A1B9A", 
                    width=200, height=40, font=("Arial", 11, "bold")).pack(side="left", padx=5)
        
        ctk.CTkButton(button_frame, text="📊 Ver Historial Completo", 
                    command=lambda: [ventana_div.destroy(), self.ver_commits_detallados()],
                    fg_color="#00897B", width=180, height=40).pack(side="left", padx=5)
        
        ctk.CTkButton(button_frame, text="✅ Continuar Sin Merge", 
                    command=ventana_div.destroy,
                    fg_color="gray", width=180, height=40).pack(side="left", padx=5)

    def _comparar_archivo_entre_ramas(self, archivo, rama1, rama2, info):
        """Muestra comparación de un archivo entre dos ramas"""
        ventana_comp = ctk.CTkToplevel(self.root)
        ventana_comp.title(f"🔍 Comparar: {archivo}")
        ventana_comp.geometry("1100x700")
        ventana_comp.transient(self.root)
        ventana_comp.attributes('-topmost', True)
        
        ctk.CTkLabel(ventana_comp, text=f"🔍 Comparación: {archivo}", 
                    font=("Arial", 14, "bold")).pack(pady=15)
        
        # Info del archivo
        info_frame = ctk.CTkFrame(ventana_comp, fg_color="#2B2B2B")
        info_frame.pack(fill="x", padx=20, pady=10)
        
        info_rama1 = info.get(rama1, {})
        info_rama2 = info.get(rama2, {})
        
        info_text = f"📍 {rama1}: {info_rama1.get('hash', 'N/A')} | {info_rama1.get('fecha', 'N/A')}\n"
        info_text += f"📍 {rama2}: {info_rama2.get('hash', 'N/A')} | {info_rama2.get('fecha', 'N/A')}"
        
        ctk.CTkLabel(info_frame, text=info_text, 
                    font=("Arial", 10), justify="left").pack(pady=8, padx=10)
        
        # Contenido de ambas versiones
        contenido_frame = ctk.CTkFrame(ventana_comp)
        contenido_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Rama 1
        frame_rama1 = ctk.CTkFrame(contenido_frame)
        frame_rama1.pack(side="left", fill="both", expand=True, padx=5)
        
        ctk.CTkLabel(frame_rama1, text=f"📄 Versión en {rama1}", 
                    font=("Arial", 11, "bold")).pack(pady=5)
        
        text_rama1 = ctk.CTkTextbox(frame_rama1, font=("Courier", 9), wrap="none")
        text_rama1.pack(fill="both", expand=True)
        
        contenido1 = self.proyecto.get_contenido_archivo_en_rama(archivo, rama1)
        if contenido1:
            text_rama1.insert("1.0", contenido1)
        else:
            text_rama1.insert("1.0", "[Archivo no disponible en esta rama]")
        text_rama1.configure(state="disabled")
        
        # Rama 2
        frame_rama2 = ctk.CTkFrame(contenido_frame)
        frame_rama2.pack(side="left", fill="both", expand=True, padx=5)
        
        ctk.CTkLabel(frame_rama2, text=f"📄 Versión en {rama2}", 
                    font=("Arial", 11, "bold")).pack(pady=5)
        
        text_rama2 = ctk.CTkTextbox(frame_rama2, font=("Courier", 9), wrap="none")
        text_rama2.pack(fill="both", expand=True)
        
        contenido2 = self.proyecto.get_contenido_archivo_en_rama(archivo, rama2)
        if contenido2:
            text_rama2.insert("1.0", contenido2)
        else:
            text_rama2.insert("1.0", "[Archivo no disponible en esta rama]")
        text_rama2.configure(state="disabled")
        
        # Botones
        button_frame = ctk.CTkFrame(ventana_comp)
        button_frame.pack(pady=10)
        
        ctk.CTkButton(button_frame, text="❌ Cerrar", 
                    command=ventana_comp.destroy,
                    fg_color="gray", width=120).pack()


    def fetch(self):
        if not self.proyecto or not self.proyecto.repo:
            messagebox.showwarning("Sin Git", "No hay repositorio Git inicializado.")
            return
        
        print("🔄 Haciendo fetch...")
        resultado = self.proyecto.fetch()
        
        if resultado == True:
            messagebox.showinfo("Fetch exitoso", 
                "✅ Fetch realizado correctamente.\n\n"
                "Se actualizaron las referencias remotas.")
        else:
            messagebox.showerror("Error Fetch", f"Error al hacer fetch:\n{resultado}")


# ======================= Metodos Merge =======================
    def merge_ramas(self):
        """Interfaz principal para realizar merge entre ramas"""
        if not self.proyecto or not self.proyecto.repo:
            messagebox.showwarning("Sin Git", "No hay repositorio Git inicializado.")
            return
        
        # Verificar si hay merge en progreso
        if self.proyecto.hay_merge_en_progreso():
            self._gestionar_merge_en_progreso()
            return
        
        # Obtener ramas disponibles
        ramas_info = self.proyecto.listar_ramas()
        ramas_locales = ramas_info.get('locales', [])
        
        if len(ramas_locales) < 2:
            messagebox.showinfo("Pocas ramas", 
                "Necesitás al menos 2 ramas para hacer merge.\n"
                "Creá una nueva rama primero.")
            return
        
        # Mostrar ventana de selección de rama
        ventana_merge = ctk.CTkToplevel(self.root)
        ventana_merge.title("🔀 Merge de Ramas")
        ventana_merge.geometry("600x550")
        ventana_merge.transient(self.root)
        ventana_merge.attributes('-topmost', True)
        ventana_merge.grab_set()
        
        ctk.CTkLabel(ventana_merge, text="🔀 Merge - Fusionar Ramas", 
                    font=("Arial", 16, "bold")).pack(pady=15)
        
        rama_actual = self.proyecto.get_rama_actual()
        
        # Frame de información
        info_frame = ctk.CTkFrame(ventana_merge, fg_color="#1E3A5F")
        info_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(info_frame, text=f"📍 Rama actual (destino): {rama_actual}", 
                    font=("Arial", 12, "bold"), text_color="#90EE90").pack(pady=8)
        
        ctk.CTkLabel(ventana_merge, 
                    text="Seleccioná la rama que querés fusionar en la rama actual:", 
                    font=("Arial", 11)).pack(pady=10)
        
        # Explicación del merge
        explicacion = ctk.CTkFrame(ventana_merge, fg_color="#2B2B2B")
        explicacion.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(explicacion, 
                    text="ℹ️ El merge combinará los cambios de la rama seleccionada\n"
                        f"con tu rama actual ({rama_actual}).\n"
                        "Si hay conflictos, deberás resolverlos manualmente.", 
                    font=("Arial", 9), text_color="#87CEEB", 
                    justify="left").pack(pady=8, padx=10)
        
        # Lista de ramas
        scroll_frame = ctk.CTkScrollableFrame(ventana_merge, width=550, height=200)
        scroll_frame.pack(pady=10, padx=20)
        
        rama_seleccionada = {"nombre": None}
        
        def seleccionar_rama(rama):
            rama_seleccionada["nombre"] = rama
        
        # Mostrar solo ramas diferentes a la actual
        ramas_disponibles = [r for r in ramas_locales if r != rama_actual]
        
        if not ramas_disponibles:
            ctk.CTkLabel(scroll_frame, text="No hay otras ramas para fusionar", 
                        font=("Arial", 11), text_color="gray").pack(pady=20)
        else:
            for rama in ramas_disponibles:
                rama_frame = ctk.CTkFrame(scroll_frame, fg_color="#1E1E1E")
                rama_frame.pack(fill="x", pady=2, padx=5)
                
                radio = ctk.CTkRadioButton(rama_frame, text="", value=rama,
                                        command=lambda r=rama: seleccionar_rama(r))
                radio.pack(side="left", padx=5)
                
                ctk.CTkLabel(rama_frame, text=f"🌿 {rama}", 
                            font=("Arial", 11)).pack(side="left", padx=10)
        
        def confirmar_merge():
            if not rama_seleccionada["nombre"]:
                messagebox.showwarning("Sin selección", "Seleccioná una rama para fusionar.")
                return
            
            rama_origen = rama_seleccionada["nombre"]
            
            respuesta = messagebox.askyesno("Confirmar Merge", 
                f"¿Fusionar la rama '{rama_origen}' en '{rama_actual}'?\n\n"
                f"Esto combinará los cambios de '{rama_origen}' en tu rama actual.\n\n"
                "⚠️ Asegurate de haber commiteado todos tus cambios antes de continuar.")
            
            if not respuesta:
                return
            
            ventana_merge.destroy()
            self._ejecutar_merge(rama_origen)
        
        # Botones
        button_frame = ctk.CTkFrame(ventana_merge, fg_color="transparent")
        button_frame.pack(pady=15)
        
        ctk.CTkButton(button_frame, text="🔀 Realizar Merge", 
                    command=confirmar_merge,
                    fg_color="#7B1FA2", hover_color="#6A1B9A", 
                    width=150, height=40, font=("Arial", 12, "bold")).pack(side="left", padx=5)
        
        ctk.CTkButton(button_frame, text="❌ Cancelar", 
                    command=ventana_merge.destroy,
                    fg_color="gray", width=120, height=40).pack(side="left", padx=5)

    def _ejecutar_merge(self, rama_origen):
        """Ejecuta el merge y maneja el resultado"""
        print(f"🔀 Iniciando merge de '{rama_origen}' en '{self.proyecto.get_rama_actual()}'")
        
        ventana_progreso = self._crear_ventana_progreso(
            "🔀 Realizando merge...",
            f"Fusionando rama '{rama_origen}'...\nEsto puede tomar unos momentos."
        )
        
        def merge_thread():
            resultado = self.proyecto.merge_rama(rama_origen)
            self.root.after(0, lambda: self._procesar_resultado_merge(resultado, rama_origen, ventana_progreso))
        
        threading.Thread(target=merge_thread, daemon=True).start()

    def _procesar_resultado_merge(self, resultado, rama_origen, ventana_progreso):
        """Procesa el resultado del merge"""
        ventana_progreso.destroy()
        
        if resultado == True:
            # Merge exitoso sin conflictos
            ventana_exito = ctk.CTkToplevel(self.root)
            ventana_exito.title("✅ Merge Exitoso")
            ventana_exito.geometry("500x300")
            ventana_exito.transient(self.root)
            ventana_exito.attributes('-topmost', True)
            ventana_exito.grab_set()
            
            ctk.CTkLabel(ventana_exito, text="✅ Merge Completado", 
                        font=("Arial", 16, "bold"), text_color="green").pack(pady=20)
            
            rama_actual = self.proyecto.get_rama_actual()
            ctk.CTkLabel(ventana_exito, 
                        text=f"La rama '{rama_origen}' se fusionó exitosamente\n"
                            f"en la rama '{rama_actual}'.\n\n"
                            "No hubo conflictos.", 
                        font=("Arial", 11), justify="center").pack(pady=10)
            
            ctk.CTkLabel(ventana_exito, 
                        text="¿Querés hacer push de los cambios?", 
                        font=("Arial", 10)).pack(pady=10)
            
            def hacer_push():
                ventana_exito.destroy()
                self.push()
            
            btn_frame = ctk.CTkFrame(ventana_exito, fg_color="transparent")
            btn_frame.pack(pady=15)
            
            ctk.CTkButton(btn_frame, text="⬆️ Sí, Push", 
                        command=hacer_push,
                        fg_color="blue", width=120).pack(side="left", padx=5)
            
            ctk.CTkButton(btn_frame, text="❌ No, Después", 
                        command=ventana_exito.destroy,
                        fg_color="gray", width=120).pack(side="left", padx=5)
            
            self.actualizar_rama_display()
            self.ver_archivos()
            
        else:
            # Verificar si hay conflictos
            if "conflict" in resultado.lower() or "merge conflict" in resultado.lower():
                self._gestionar_merge_en_progreso()
            else:
                messagebox.showerror("Error en Merge", 
                    f"Error al realizar el merge:\n\n{resultado}")

    def _gestionar_merge_en_progreso(self):
        """Gestiona un merge con conflictos"""
        conflictos = self.proyecto.get_conflictos()
        
        ventana_conflictos = ctk.CTkToplevel(self.root)
        ventana_conflictos.title("⚠️ Conflictos de Merge")
        ventana_conflictos.geometry("800x600")
        ventana_conflictos.transient(self.root)
        ventana_conflictos.attributes('-topmost', True)
        ventana_conflictos.grab_set()
        
        ctk.CTkLabel(ventana_conflictos, text="⚠️ Merge con Conflictos", 
                    font=("Arial", 16, "bold"), text_color="orange").pack(pady=15)
        
        info_frame = ctk.CTkFrame(ventana_conflictos, fg_color="#3D2B1F")
        info_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(info_frame, 
                    text=f"⚠️ Se encontraron {len(conflictos)} archivo(s) con conflictos.\n"
                        "Debés resolver los conflictos antes de continuar.", 
                    font=("Arial", 11), text_color="orange").pack(pady=10, padx=10)
        
        # Instrucciones
        instrucciones = ctk.CTkFrame(ventana_conflictos, fg_color="#2B2B2B")
        instrucciones.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(instrucciones, 
                    text="📋 Opciones para resolver conflictos:\n\n"
                        "• 'Ours': Mantener la versión de tu rama actual\n"
                        "• 'Theirs': Aceptar la versión de la rama que estás fusionando\n"
                        "• Manual: Editar el archivo manualmente en tu editor", 
                    font=("Arial", 9), text_color="#87CEEB", 
                    justify="left").pack(pady=8, padx=10)
        
        # Lista de conflictos
        ctk.CTkLabel(ventana_conflictos, text="Archivos con conflictos:", 
                    font=("Arial", 12, "bold")).pack(pady=10)
        
        scroll_frame = ctk.CTkScrollableFrame(ventana_conflictos, width=750, height=250)
        scroll_frame.pack(pady=5, padx=20)
        
        archivos_resueltos = {}
        
        for archivo in conflictos:
            archivo_frame = ctk.CTkFrame(scroll_frame, fg_color="#3D1F1F")
            archivo_frame.pack(fill="x", pady=3, padx=5)
            
            ctk.CTkLabel(archivo_frame, text=f"⚠️ {archivo}", 
                        font=("Arial", 10, "bold"), 
                        text_color="#FF6B6B", anchor="w", width=400).pack(side="left", padx=10)
            
            def resolver_ours(arch=archivo):
                resultado = self.proyecto.resolver_conflicto_archivo(arch, 'ours')
                if resultado == True:
                    archivos_resueltos[arch] = 'ours'
                    messagebox.showinfo("Resuelto", f"✅ Conflicto resuelto (manteniendo tu versión):\n{arch}")
                    ventana_conflictos.destroy()
                    self._gestionar_merge_en_progreso()
                else:
                    messagebox.showerror("Error", f"Error resolviendo conflicto:\n{resultado}")
            
            def resolver_theirs(arch=archivo):
                resultado = self.proyecto.resolver_conflicto_archivo(arch, 'theirs')
                if resultado == True:
                    archivos_resueltos[arch] = 'theirs'
                    messagebox.showinfo("Resuelto", f"✅ Conflicto resuelto (aceptando versión entrante):\n{arch}")
                    ventana_conflictos.destroy()
                    self._gestionar_merge_en_progreso()
                else:
                    messagebox.showerror("Error", f"Error resolviendo conflicto:\n{resultado}")
            
            def abrir_archivo(arch=archivo):
                ruta_completa = os.path.join(self.proyecto.path, arch)
                try:
                    os.system(f'code "{ruta_completa}"')
                    messagebox.showinfo("Editor", 
                        f"Archivo abierto en VS Code:\n{arch}\n\n"
                        "Resuelve los conflictos manualmente:\n"
                        "• Busca los marcadores <<<<<<, =======, >>>>>>>\n"
                        "• Edita el archivo dejando solo el código que querés\n"
                        "• Guarda el archivo\n"
                        "• Vuelve a esta ventana y hace 'Refrescar'")
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo abrir el archivo:\n{e}")
            
            btn_frame = ctk.CTkFrame(archivo_frame, fg_color="transparent")
            btn_frame.pack(side="right", padx=5)
            
            ctk.CTkButton(btn_frame, text="Ours", command=resolver_ours, 
                        fg_color="#2E7D32", width=70, height=25, 
                        font=("Arial", 9)).pack(side="left", padx=2)
            
            ctk.CTkButton(btn_frame, text="Theirs", command=resolver_theirs, 
                        fg_color="#1565C0", width=70, height=25, 
                        font=("Arial", 9)).pack(side="left", padx=2)
            
            ctk.CTkButton(btn_frame, text="✏️ Editar", command=abrir_archivo, 
                        fg_color="#F57C00", width=70, height=25, 
                        font=("Arial", 9)).pack(side="left", padx=2)
        
        # Botones principales
        button_frame = ctk.CTkFrame(ventana_conflictos, fg_color="transparent")
        button_frame.pack(pady=15)
        
        def refrescar():
            ventana_conflictos.destroy()
            self._gestionar_merge_en_progreso()
        
        def continuar_merge():
            conflictos_restantes = self.proyecto.get_conflictos()
            
            if conflictos_restantes:
                messagebox.showwarning("Conflictos pendientes", 
                    f"Todavía hay {len(conflictos_restantes)} archivo(s) con conflictos sin resolver.\n\n"
                    "Debés resolver todos los conflictos antes de continuar.")
                return
            
            respuesta = messagebox.askyesno("Continuar Merge", 
                "¿Todos los conflictos fueron resueltos?\n\n"
                "Esto completará el merge y creará un commit de merge.")
            
            if not respuesta:
                return
            
            ventana_conflictos.destroy()
            
            resultado = self.proyecto.continuar_merge()
            
            if resultado == True:
                messagebox.showinfo("Merge Completado", 
                    "✅ Merge completado exitosamente.\n\n"
                    "Todos los conflictos fueron resueltos y el commit de merge fue creado.")
                self.actualizar_rama_display()
                self.ver_archivos()
            else:
                messagebox.showerror("Error", f"Error completando merge:\n{resultado}")
        
        def abortar():
            respuesta = messagebox.askyesno("Abortar Merge", 
                "⚠️ ¿Abortar el merge?\n\n"
                "Esto descartará todos los cambios del merge\n"
                "y volverá al estado anterior.")
            
            if not respuesta:
                return
            
            resultado = self.proyecto.abortar_merge()
            
            if resultado == True:
                messagebox.showinfo("Merge Abortado", 
                    "✅ El merge fue abortado.\n\n"
                    "Tu repositorio volvió al estado anterior al merge.")
                ventana_conflictos.destroy()
                self.actualizar_rama_display()
                self.ver_archivos()
            else:
                messagebox.showerror("Error", f"Error abortando merge:\n{resultado}")
        
        ctk.CTkButton(button_frame, text="🔄 Refrescar", 
                    command=refrescar,
                    fg_color="#00897B", width=120, height=35).pack(side="left", padx=5)
        
        ctk.CTkButton(frame_proyecto, text="💻 Terminal", command=self.abrir_terminal_en_rama, 
                    width=100, fg_color="#424242").grid(row=0, column=5, padx=3, pady=5)

        ctk.CTkButton(button_frame, text="✅ Continuar Merge", 
                    command=continuar_merge,
                    fg_color="green", hover_color="darkgreen", 
                    width=150, height=35, font=("Arial", 11, "bold")).pack(side="left", padx=5)
        
        ctk.CTkButton(button_frame, text="❌ Abortar Merge", 
                    command=abortar,
                    fg_color="red", hover_color="darkred", 
                    width=130, height=35).pack(side="left", padx=5)

    # ======================= Arriba Metodos Merge =======================
    def abrir_terminal_en_rama(self):
        """Abre una terminal en el directorio del proyecto mostrando la rama"""
        if not self.proyecto:
            messagebox.showwarning("Sin proyecto", "Primero seleccioná un directorio de proyecto.")
            return
        
        path = self.proyecto.path
        rama_actual = self.proyecto.get_rama_actual() if self.proyecto.repo else "Sin repo"
        
        messagebox.showinfo("Terminal", 
            f"📁 Abriendo terminal en:\n{path}\n\n"
            f"🌿 Rama activa: {rama_actual}\n\n"
            "Podés verificar la rama con:\ngit branch\n\n"
            "Y ver el estado con:\ngit status")
        
        try:
            # Windows
            if os.name == 'nt':
                os.system(f'start cmd /K "cd /d {path} && git branch"')
            # Linux/Mac
            else:
                os.system(f'gnome-terminal --working-directory="{path}" -- bash -c "git branch; exec bash"')
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la terminal:\n{e}")

    # ==================== MÉTODOS AUXILIARES ====================

    def _crear_ventana_progreso(self, titulo, mensaje):
        ventana = ctk.CTkToplevel(self.root)
        ventana.title(titulo)
        ventana.geometry("500x150")
        ventana.transient(self.root)
        ventana.grab_set()
        ventana.attributes('-topmost', True)
        
        ctk.CTkLabel(ventana, text=titulo, 
                    font=("Arial", 13, "bold")).pack(pady=20)
        ctk.CTkLabel(ventana, text=mensaje).pack()
        
        progress_bar = ctk.CTkProgressBar(ventana, mode="indeterminate")
        progress_bar.pack(pady=10, padx=20, fill="x")
        progress_bar.start()
        
        self.root.update()
        ventana.update()
        
        return ventana

    def _manejar_error(self, error, ventana_progreso):
        ventana_progreso.destroy()
        messagebox.showerror("Error", f"Error inesperado:\n{error}")

    def _mostrar_ventana_commits_archivo(self, archivo, commits):
        ventana = ctk.CTkToplevel(self.root)
        ventana.title(f"📂 Historial: {archivo}")
        ventana.geometry("1000x550")
        ventana.transient(self.root)
        ventana.attributes('-topmost', True)
        
        frame_info = ctk.CTkFrame(ventana, fg_color="#2B5B5B")
        frame_info.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(frame_info, text=f"📁 Archivo: {archivo}", 
                    font=("Arial", 12, "bold")).pack(side="left", padx=10)
        ctk.CTkLabel(frame_info, text=f"📊 Commits: {len(commits)}", 
                    font=("Arial", 11)).pack(side="right", padx=10)
        
        scrollable = ctk.CTkScrollableFrame(ventana, width=950, height=350)
        scrollable.pack(fill="both", expand=True, padx=10, pady=5)
        
        header = ctk.CTkFrame(scrollable, fg_color="#1E3A5F")
        header.pack(fill="x", pady=2)
        ctk.CTkLabel(header, text="Hash", font=("Arial", 10, "bold"), width=80).pack(side="left", padx=2)
        ctk.CTkLabel(header, text="Cambios", font=("Arial", 10, "bold"), width=120).pack(side="left", padx=2)
        ctk.CTkLabel(header, text="Mensaje", font=("Arial", 10, "bold"), width=250).pack(side="left", padx=2)
        ctk.CTkLabel(header, text="Autor", font=("Arial", 10, "bold"), width=120).pack(side="left", padx=2)
        ctk.CTkLabel(header, text="Fecha", font=("Arial", 10, "bold"), width=130).pack(side="left", padx=2)
        
        for commit in commits:
            cframe = ctk.CTkFrame(scrollable, fg_color="#1E1E1E")
            cframe.pack(fill="x", pady=1)
            
            ctk.CTkLabel(cframe, text=commit['hash'], font=("Courier", 9), width=80).pack(side="left", padx=2)
            ctk.CTkLabel(cframe, text=commit['cambios'], font=("Arial", 9), width=120).pack(side="left", padx=2)
            msg = commit['mensaje'][:35] + "..." if len(commit['mensaje']) > 35 else commit['mensaje']
            ctk.CTkLabel(cframe, text=msg, font=("Arial", 9), width=250, anchor="w").pack(side="left", padx=2)
            autor = commit['autor'].split('<')[0].strip()
            ctk.CTkLabel(cframe, text=autor, font=("Arial", 9), width=120, anchor="w").pack(side="left", padx=2)
            ctk.CTkLabel(cframe, text=commit['fecha'], font=("Arial", 9), width=130).pack(side="left", padx=2)
        
        frame_btn = ctk.CTkFrame(ventana)
        frame_btn.pack(fill="x", padx=10, pady=10)
        ctk.CTkButton(frame_btn, text="❌ Cerrar", command=ventana.destroy, 
                     fg_color="gray", width=100).pack(side="right", padx=5)

    # ==================== HISTORIAL Y AVANZADO ====================

    def ver_commits_detallados(self):
        if not self.proyecto or not self.proyecto.repo:
            messagebox.showwarning("Sin Git", "No hay repositorio Git inicializado.")
            return
        
        commits = self.proyecto.get_commits_detallados(30)
        if not commits:
            messagebox.showinfo("Sin commits", "No hay commits en este repositorio.")
            return
        
        self._mostrar_ventana_commits_detallados(commits)

    def _mostrar_ventana_commits_detallados(self, commits):
        ventana = ctk.CTkToplevel(self.root)
        ventana.title("🕐 Historial de Commits")
        ventana.geometry("950x550")
        ventana.transient(self.root)
        ventana.attributes('-topmost', True)
        
        frame_info = ctk.CTkFrame(ventana, fg_color="#2B2B2B")
        frame_info.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(frame_info, text=f"📊 Total de commits: {len(commits)}", 
                    font=("Arial", 12, "bold")).pack(side="left", padx=10)
        
        scrollable_commits = ctk.CTkScrollableFrame(ventana, width=900, height=350)
        scrollable_commits.pack(fill="both", expand=True, padx=10, pady=5)
        
        header_frame = ctk.CTkFrame(scrollable_commits, fg_color="#1E3A5F")
        header_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(header_frame, text="Hash", font=("Arial", 10, "bold"), width=80).pack(side="left", padx=2)
        ctk.CTkLabel(header_frame, text="Mensaje", font=("Arial", 10, "bold"), width=300).pack(side="left", padx=2)
        ctk.CTkLabel(header_frame, text="Autor", font=("Arial", 10, "bold"), width=150).pack(side="left", padx=2)
        ctk.CTkLabel(header_frame, text="Fecha", font=("Arial", 10, "bold"), width=130).pack(side="left", padx=2)
        ctk.CTkLabel(header_frame, text="Tiempo", font=("Arial", 10, "bold"), width=100).pack(side="left", padx=2)
        
        commit_vars = {}
        selected_commit = {"data": None}
        
        def select_commit(commit_data):
            selected_commit["data"] = commit_data
        
        for commit in commits:
            commit_frame = ctk.CTkFrame(scrollable_commits, fg_color="#1E1E1E")
            commit_frame.pack(fill="x", pady=1)
            
            radio_var = ctk.StringVar(value="")
            radio = ctk.CTkRadioButton(commit_frame, text="", variable=radio_var, value=commit['hash'],
                                       command=lambda c=commit: select_commit(c), width=20)
            radio.pack(side="left", padx=2)
            commit_vars[commit['hash']] = (radio_var, commit)
            
            ctk.CTkLabel(commit_frame, text=commit['hash'], font=("Courier", 9), width=80).pack(side="left", padx=2)
            mensaje_corto = commit['mensaje'][:45] + "..." if len(commit['mensaje']) > 45 else commit['mensaje']
            ctk.CTkLabel(commit_frame, text=mensaje_corto, font=("Arial", 9), width=300, anchor="w").pack(side="left", padx=2)
            autor_corto = commit['autor'].split('<')[0].strip()
            ctk.CTkLabel(commit_frame, text=autor_corto, font=("Arial", 9), width=150, anchor="w").pack(side="left", padx=2)
            ctk.CTkLabel(commit_frame, text=commit['fecha'], font=("Arial", 9), width=130).pack(side="left", padx=2)
            ctk.CTkLabel(commit_frame, text=commit['fecha_relativa'], font=("Arial", 9), 
                        width=100, text_color="#87CEEB").pack(side="left", padx=2)
        
        frame_botones = ctk.CTkFrame(ventana)
        frame_botones.pack(fill="x", padx=10, pady=10)
        
        def ver_detalles():
            if not selected_commit["data"]:
                messagebox.showwarning("Sin selección", "Seleccioná un commit.")
                return
            
            commit = selected_commit["data"]
            detalles = f"""📋 DETALLES DEL COMMIT
            
🔹 Hash: {commit['hash_completo']}
🔹 Hash corto: {commit['hash']}
📝 Mensaje: {commit['mensaje']}
👤 Autor: {commit['autor']}
📅 Fecha: {commit['fecha']}
⏰ Hace: {commit['fecha_relativa']}"""
            
            messagebox.showinfo(f"Commit {commit['hash']}", detalles)
        
        def reset_soft():
            if not selected_commit["data"]:
                messagebox.showwarning("Sin selección", "Seleccioná un commit.")
                return
            
            commit = selected_commit["data"]
            respuesta = messagebox.askyesno("Reset Soft", 
                f"¿Volver al commit {commit['hash']}?\n\n"
                f"'{commit['mensaje']}'\n\n"
                "RESET SOFT: Mantiene los cambios en staging area.")
            
            if respuesta:
                resultado = self.proyecto.reset_to_commit(commit['hash_completo'], "soft")
                if resultado == True:
                    messagebox.showinfo("Reset exitoso", "✅ Reset soft realizado.")
                    ventana.destroy()
                    self.actualizar_rama_display()
                    self.ver_archivos()
                else:
                    messagebox.showerror("Error", f"Error en reset:\n{resultado}")
        
        def reset_hard():
            if not selected_commit["data"]:
                messagebox.showwarning("Sin selección", "Seleccioná un commit.")
                return
            
            commit = selected_commit["data"]
            respuesta = messagebox.askyesno("Reset Hard - ¡PELIGRO!", 
                f"¿Volver al commit {commit['hash']}?\n\n"
                f"'{commit['mensaje']}'\n\n"
                "⚠️ RESET HARD: ¡ELIMINA TODOS LOS CAMBIOS!\n"
                "Esta acción NO se puede deshacer.\n\n"
                "¿Estás seguro?")
            
            if respuesta:
                respuesta2 = messagebox.askyesno("¿Estás 100% seguro?", 
                    "⚠️ ÚLTIMA ADVERTENCIA ⚠️\n\n"
                    "Se perderán TODOS los cambios no commiteados.\n"
                    "Esta acción es IRREVERSIBLE.\n\n"
                    "¿Continuar con RESET HARD?")
                
                if respuesta2:
                    resultado = self.proyecto.reset_to_commit(commit['hash_completo'], "hard")
                    if resultado == True:
                        messagebox.showinfo("Reset exitoso", "✅ Reset hard realizado.")
                        ventana.destroy()
                        self.actualizar_rama_display()
                        self.ver_archivos()
                    else:
                        messagebox.showerror("Error", f"Error en reset:\n{resultado}")
        
        ctk.CTkButton(frame_botones, text="📄 Ver Detalles", command=ver_detalles, 
                     fg_color="#1E90FF", width=120).pack(side="left", padx=5)
        ctk.CTkButton(frame_botones, text="🔄 Reset Soft", command=reset_soft, 
                     fg_color="#FFD700", text_color="black", width=120).pack(side="left", padx=5)
        ctk.CTkButton(frame_botones, text="⚠️ Reset Hard", command=reset_hard, 
                     fg_color="red", width=120).pack(side="left", padx=5)
        ctk.CTkButton(frame_botones, text="❌ Cerrar", command=ventana.destroy, 
                     fg_color="gray", width=100).pack(side="right", padx=5)

    def cherry_pick(self):
        if not self.proyecto or not self.proyecto.repo:
            messagebox.showwarning("Sin Git", "No hay repositorio Git inicializado.")
            return
        
        commits = self.proyecto.get_commits_detallados(50)
        if not commits:
            messagebox.showinfo("Sin commits", "No hay commits disponibles.")
            return
        
        ventana_cherry = ctk.CTkToplevel(self.root)
        ventana_cherry.title("🍒 Cherry Pick")
        ventana_cherry.geometry("950x600")
        ventana_cherry.transient(self.root)
        ventana_cherry.attributes('-topmost', True)
        ventana_cherry.grab_set()
        
        ctk.CTkLabel(ventana_cherry, text="🍒 Cherry Pick - Aplicar Commits", 
                    font=("Arial", 16, "bold")).pack(pady=15)
        
        rama_actual = self.proyecto.get_rama_actual()
        ctk.CTkLabel(ventana_cherry, 
                    text=f"Se aplicarán los commits seleccionados a la rama: {rama_actual}", 
                    font=("Arial", 11), text_color="#90EE90").pack(pady=5)
        
        ctk.CTkLabel(ventana_cherry, 
                    text="⚠️ Cherry-pick aplica cambios de un commit a tu rama actual sin hacer merge", 
                    font=("Arial", 9), text_color="orange").pack(pady=3)
        
        frame_info = ctk.CTkFrame(ventana_cherry, fg_color="#2B2B2B")
        frame_info.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(frame_info, text=f"📊 Total commits: {len(commits)}", 
                    font=("Arial", 11)).pack(side="left", padx=10)
        
        scrollable_cherry = ctk.CTkScrollableFrame(ventana_cherry, width=900, height=350)
        scrollable_cherry.pack(fill="both", expand=True, padx=10, pady=5)
        
        header = ctk.CTkFrame(scrollable_cherry, fg_color="#1E3A5F")
        header.pack(fill="x", pady=2)
        ctk.CTkLabel(header, text="Hash", font=("Arial", 10, "bold"), width=80).pack(side="left", padx=2)
        ctk.CTkLabel(header, text="Mensaje", font=("Arial", 10, "bold"), width=350).pack(side="left", padx=2)
        ctk.CTkLabel(header, text="Autor", font=("Arial", 10, "bold"), width=150).pack(side="left", padx=2)
        ctk.CTkLabel(header, text="Fecha", font=("Arial", 10, "bold"), width=130).pack(side="left", padx=2)
        ctk.CTkLabel(header, text="Tiempo", font=("Arial", 10, "bold"), width=100).pack(side="left", padx=2)
        
        commits_seleccionados = []
        
        def toggle_commit(commit, var):
            if var.get():
                if commit not in commits_seleccionados:
                    commits_seleccionados.append(commit)
            else:
                if commit in commits_seleccionados:
                    commits_seleccionados.remove(commit)
        
        for commit in commits:
            commit_frame = ctk.CTkFrame(scrollable_cherry, fg_color="#1E1E1E")
            commit_frame.pack(fill="x", pady=1)
            
            var = ctk.BooleanVar()
            checkbox = ctk.CTkCheckBox(commit_frame, text="", variable=var, width=30,
                                       command=lambda c=commit, v=var: toggle_commit(c, v))
            checkbox.pack(side="left", padx=2)
            
            ctk.CTkLabel(commit_frame, text=commit['hash'], font=("Courier", 9), width=80).pack(side="left", padx=2)
            mensaje = commit['mensaje'][:50] + "..." if len(commit['mensaje']) > 50 else commit['mensaje']
            ctk.CTkLabel(commit_frame, text=mensaje, font=("Arial", 9), width=350, anchor="w").pack(side="left", padx=2)
            autor = commit['autor'].split('<')[0].strip()
            ctk.CTkLabel(commit_frame, text=autor, font=("Arial", 9), width=150, anchor="w").pack(side="left", padx=2)
            ctk.CTkLabel(commit_frame, text=commit['fecha'], font=("Arial", 9), width=130).pack(side="left", padx=2)
            ctk.CTkLabel(commit_frame, text=commit['fecha_relativa'], font=("Arial", 9), 
                        width=100, text_color="#87CEEB").pack(side="left", padx=2)
        
        def aplicar_cherry_pick():
            if not commits_seleccionados:
                messagebox.showwarning("Sin selección", "Seleccioná al menos un commit.")
                return
            
            respuesta = messagebox.askyesno("Confirmar Cherry Pick",
                f"¿Aplicar {len(commits_seleccionados)} commit(s) a la rama '{rama_actual}'?\n\n"
                "Esto aplicará los cambios de esos commits a tu rama actual.")
            
            if not respuesta:
                return
            
            ventana_cherry.destroy()
            
            exitos = []
            errores = []
            
            for commit in commits_seleccionados:
                print(f"🍒 Cherry-picking: {commit['hash']} - {commit['mensaje']}")
                resultado = self.proyecto.cherry_pick_commit(commit['hash_completo'])
                
                if resultado == True:
                    exitos.append(commit['hash'])
                else:
                    errores.append((commit['hash'], resultado))
            
            ventana_resultado = ctk.CTkToplevel(self.root)
            ventana_resultado.title("🍒 Resultado Cherry Pick")
            ventana_resultado.geometry("600x400")
            ventana_resultado.transient(self.root)
            ventana_resultado.attributes('-topmost', True)
            ventana_resultado.grab_set()
            
            if errores:
                ctk.CTkLabel(ventana_resultado, text="⚠️ Cherry Pick Completado con Errores", 
                            font=("Arial", 14, "bold"), text_color="orange").pack(pady=15)
            else:
                ctk.CTkLabel(ventana_resultado, text="✅ Cherry Pick Exitoso", 
                            font=("Arial", 14, "bold"), text_color="green").pack(pady=15)
            
            ctk.CTkLabel(ventana_resultado, text=f"✅ Exitosos: {len(exitos)} | ❌ Errores: {len(errores)}", 
                        font=("Arial", 12)).pack(pady=5)
            
            scroll_result = ctk.CTkScrollableFrame(ventana_resultado, width=550, height=250)
            scroll_result.pack(pady=10, padx=20)
            
            if exitos:
                ctk.CTkLabel(scroll_result, text="✅ Commits aplicados:", 
                            font=("Arial", 11, "bold"), text_color="green").pack(anchor="w", pady=5)
                for hash_commit in exitos:
                    ctk.CTkLabel(scroll_result, text=f"  ✓ {hash_commit}", 
                                font=("Courier", 9), text_color="#90EE90").pack(anchor="w", pady=1)
            
            if errores:
                ctk.CTkLabel(scroll_result, text="❌ Commits con errores:", 
                            font=("Arial", 11, "bold"), text_color="red").pack(anchor="w", pady=5)
                for hash_commit, error in errores:
                    ctk.CTkLabel(scroll_result, text=f"  ✗ {hash_commit}", 
                                font=("Courier", 9), text_color="#FF6B6B").pack(anchor="w", pady=1)
                    ctk.CTkLabel(scroll_result, text=f"     {str(error)[:80]}", 
                                font=("Arial", 8), text_color="gray").pack(anchor="w", pady=1)
            
            ctk.CTkButton(ventana_resultado, text="✅ Cerrar", 
                         command=ventana_resultado.destroy,
                         fg_color="green", width=120).pack(pady=15)
            
            self.actualizar_rama_display()
            self.ver_archivos()
        
        button_frame = ctk.CTkFrame(ventana_cherry, fg_color="transparent")
        button_frame.pack(pady=15)
        
        ctk.CTkButton(button_frame, text=f"🍒 Aplicar Cherry Pick", 
                     command=aplicar_cherry_pick,
                     fg_color="#D32F2F", hover_color="#B71C1C", 
                     width=180, height=40, font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="❌ Cancelar", 
                     command=ventana_cherry.destroy,
                     fg_color="gray", width=120, height=40).pack(side="left", padx=5)

    def ver_commits_por_archivo(self):
        if not self.proyecto or not self.proyecto.repo:
            messagebox.showwarning("Sin Git", "No hay repositorio Git inicializado.")
            return
        
        archivo_seleccionado = CTkInputDialog(
            parent=self.root,
            title="📂 Commits por Archivo",
            prompt="Nombre del archivo (ruta relativa):",
            initialvalue="README.md"
        ).result
        
        if not archivo_seleccionado:
            return
        
        commits = self.proyecto.get_commits_por_archivo(archivo_seleccionado, 30)
        if not commits:
            messagebox.showinfo("Sin commits", f"No hay commits que afecten el archivo '{archivo_seleccionado}'.")
            return
        
        self._mostrar_ventana_commits_archivo(archivo_seleccionado, commits)

    # ==================== TAGS ====================

    def crear_tag_version(self):
        if not self.proyecto or not self.proyecto.repo:
            messagebox.showwarning("Sin Git", "No hay repositorio Git inicializado.")
            return
        
        nombre_tag = CTkInputDialog(
            parent=self.root,
            title="🏷️ Nuevo Tag",
            prompt="Nombre del tag (ej: v1.0.0, release-2024-01):",
            initialvalue="v1.0.0"
        ).result
        
        if not nombre_tag:
            return
        
        mensaje_tag = CTkInputDialog(
            parent=self.root,
            title="🏷️ Mensaje del Tag",
            prompt="Mensaje descriptivo del tag:",
            initialvalue=f"Versión {nombre_tag}"
        ).result
        
        print(f"🏷️ Creando tag: {nombre_tag}")
        resultado = self.proyecto.crear_tag(nombre_tag, mensaje_tag)
        
        if resultado == True:
            respuesta = messagebox.askyesno("Tag creado", 
                f"✅ Tag '{nombre_tag}' creado exitosamente.\n\n¿Querés hacer push del tag al repositorio remoto?")
            
            if respuesta:
                resultado_push = self.proyecto.push_tags()
                if resultado_push == True:
                    messagebox.showinfo("Push exitoso", "✅ Tag subido al repositorio remoto.")
                else:
                    messagebox.showerror("Error Push", f"Error subiendo tag:\n{resultado_push}")
        else:
            messagebox.showerror("Error", f"Error creando tag:\n{resultado}")

    def gestionar_tags(self):
        if not self.proyecto or not self.proyecto.repo:
            messagebox.showwarning("Sin Git", "No hay repositorio Git inicializado.")
            return
        
        tags = self.proyecto.get_tags()
        
        ventana_tags = ctk.CTkToplevel(self.root)
        ventana_tags.title("🏷️ Gestión de Tags")
        ventana_tags.geometry("950x550")
        ventana_tags.transient(self.root)
        ventana_tags.attributes('-topmost', True)
        
        frame_info = ctk.CTkFrame(ventana_tags, fg_color="#5B2B2B")
        frame_info.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(frame_info, text=f"🏷️ Tags en el repositorio: {len(tags)}", 
                    font=("Arial", 12, "bold")).pack(side="left", padx=10)
        
        if not tags:
            ctk.CTkLabel(ventana_tags, text="📝 No hay tags en este repositorio.\nUsá '🚀 Crear Tag' para crear el primero.", 
                        font=("Arial", 13), text_color="gray").pack(expand=True)
            ctk.CTkButton(ventana_tags, text="❌ Cerrar", command=ventana_tags.destroy, 
                         fg_color="gray").pack(pady=10)
            return
        
        scrollable_tags = ctk.CTkScrollableFrame(ventana_tags, width=900, height=350)
        scrollable_tags.pack(fill="both", expand=True, padx=10, pady=5)
        
        header = ctk.CTkFrame(scrollable_tags, fg_color="#1E3A5F")
        header.pack(fill="x", pady=2)
        ctk.CTkLabel(header, text="Tag", font=("Arial", 10, "bold"), width=100).pack(side="left", padx=2)
        ctk.CTkLabel(header, text="Hash", font=("Arial", 10, "bold"), width=80).pack(side="left", padx=2)
        ctk.CTkLabel(header, text="Msg Tag", font=("Arial", 10, "bold"), width=150).pack(side="left", padx=2)
        ctk.CTkLabel(header, text="Msg Commit", font=("Arial", 10, "bold"), width=200).pack(side="left", padx=2)
        ctk.CTkLabel(header, text="Autor", font=("Arial", 10, "bold"), width=120).pack(side="left", padx=2)
        ctk.CTkLabel(header, text="Fecha", font=("Arial", 10, "bold"), width=130).pack(side="left", padx=2)
        
        selected_tag = {"data": None}
        
        def select_tag(tag_data):
            selected_tag["data"] = tag_data
        
        for tag in tags:
            tframe = ctk.CTkFrame(scrollable_tags, fg_color="#1E1E1E")
            tframe.pack(fill="x", pady=1)
            
            radio = ctk.CTkRadioButton(tframe, text="", value=tag['nombre'],
                                       command=lambda t=tag: select_tag(t), width=20)
            radio.pack(side="left", padx=2)
            
            ctk.CTkLabel(tframe, text=tag['nombre'], font=("Arial", 9, "bold"), 
                        width=100, text_color="#FFD700").pack(side="left", padx=2)
            ctk.CTkLabel(tframe, text=tag['hash'], font=("Courier", 9), width=80).pack(side="left", padx=2)
            msg_t = tag['mensaje_tag'][:25] + "..." if len(tag['mensaje_tag']) > 25 else tag['mensaje_tag']
            ctk.CTkLabel(tframe, text=msg_t, font=("Arial", 9), width=150).pack(side="left", padx=2)
            msg_c = tag['mensaje_commit'][:35] + "..." if len(tag['mensaje_commit']) > 35 else tag['mensaje_commit']
            ctk.CTkLabel(tframe, text=msg_c, font=("Arial", 9), width=200, anchor="w").pack(side="left", padx=2)
            autor = tag['autor'].split('<')[0].strip()
            ctk.CTkLabel(tframe, text=autor, font=("Arial", 9), width=120, anchor="w").pack(side="left", padx=2)
            ctk.CTkLabel(tframe, text=tag['fecha'], font=("Arial", 9), width=130).pack(side="left", padx=2)
        
        frame_btn = ctk.CTkFrame(ventana_tags)
        frame_btn.pack(fill="x", padx=10, pady=10)
        
        def eliminar_tag():
            if not selected_tag["data"]:
                messagebox.showwarning("Sin selección", "Seleccioná un tag.")
                return
            
            tag = selected_tag["data"]
            respuesta = messagebox.askyesno("Eliminar Tag", 
                f"¿Eliminar el tag '{tag['nombre']}'?\n\n"
                f"Hash: {tag['hash']}\n"
                f"Fecha: {tag['fecha']}\n\n"
                "⚠️ Esta acción no se puede deshacer.")
            
            if respuesta:
                resultado = self.proyecto.eliminar_tag(tag['nombre'])
                if resultado == True:
                    messagebox.showinfo("Tag eliminado", f"✅ Tag '{tag['nombre']}' eliminado.")
                    ventana_tags.destroy()
                    self.gestionar_tags()
                else:
                    messagebox.showerror("Error", f"Error eliminando tag:\n{resultado}")
        
        def push_todos():
            respuesta = messagebox.askyesno("Push Tags", 
                "¿Hacer push de todos los tags al repositorio remoto?\n\n"
                "Esto subirá todos los tags que no estén en el remoto.")
            
            if respuesta:
                resultado = self.proyecto.push_tags()
                if resultado == True:
                    messagebox.showinfo("Push exitoso", "✅ Todos los tags subidos al repositorio remoto.")
                else:
                    messagebox.showerror("Error Push", f"Error subiendo tags:\n{resultado}")
        
        ctk.CTkButton(frame_btn, text="🗑️ Eliminar Tag", command=eliminar_tag, 
                     fg_color="red", width=130).pack(side="left", padx=5)
        ctk.CTkButton(frame_btn, text="⬆️ Push Todos", command=push_todos, 
                     fg_color="blue", width=120).pack(side="left", padx=5)
        ctk.CTkButton(frame_btn, text="❌ Cerrar", command=ventana_tags.destroy, 
                     fg_color="gray", width=100).pack(side="right", padx=5)

    # ==================== GITHUB ====================

    def clonar_repositorio(self):
        url = self.url_clone_var.get().strip()
        if not url:
            messagebox.showwarning("URL vacía", "Ingresá la URL del repositorio a clonar.")
            return
        
        try:
            nombre_repo = url.split('/')[-1].replace('.git', '')
            if not nombre_repo:
                nombre_repo = "repositorio_clonado"
        except:
            nombre_repo = "repositorio_clonado"
        
        directorio_padre = filedialog.askdirectory(title="Seleccionar carpeta donde clonar")
        if not directorio_padre:
            return
        
        directorio_destino = os.path.join(directorio_padre, nombre_repo)
        
        if os.path.exists(directorio_destino):
            respuesta = messagebox.askyesno("Directorio existe", 
                f"El directorio '{nombre_repo}' ya existe.\n¿Querés continuar de todas formas?")
            if not respuesta:
                return
        
        ventana_progreso = self._crear_ventana_progreso(
            "📥 Clonando repositorio...",
            f"URL: {url[:50]}...\nEsto puede tomar varios minutos..."
        )
        
        def clonar():
            try:
                proyecto_temp = Proyecto(".")
                resultado = proyecto_temp.clonar_repo(url, directorio_destino)
                self.root.after(0, lambda: self._procesar_clonado(resultado, directorio_destino, ventana_progreso))
            except Exception as e:
                self.root.after(0, lambda: self._manejar_error(e, ventana_progreso))
        
        threading.Thread(target=clonar, daemon=True).start()

    def _procesar_clonado(self, resultado, directorio_destino, ventana_progreso):
        ventana_progreso.destroy()
        
        if resultado == True:
            self.path_var.set(directorio_destino)
            self.proyecto = Proyecto(directorio_destino)
            self.actualizar_rama_display()
            
            messagebox.showinfo("Clone exitoso", 
                f"✅ Repositorio clonado exitosamente en:\n{directorio_destino}")
            
            self.ver_archivos()
        else:
            messagebox.showerror("Error al clonar", f"❌ Error:\n{resultado}")

    def crear_repo_github(self):
        if not self.proyecto:
            messagebox.showwarning("Sin proyecto", "Primero seleccioná un directorio de proyecto.")
            return
            
        nombre = CTkInputDialog(
            parent=self.root,
            title="🌐 Nombre del Repositorio",
            prompt="Nombre para el repositorio en GitHub:",
            initialvalue=os.path.basename(self.proyecto.path)
        ).result
        
        if not nombre:
            return
            
        visibilidad = CTkChoiceDialog(
            parent=self.root,
            title="🌐 Visibilidad del Repositorio",
            prompt="Seleccioná la visibilidad del repositorio:",
            choices=["private", "public"]
        ).result
        
        if not visibilidad:
            visibilidad = "private"
            
        print(f"🌐 Creando repositorio GitHub: {nombre} ({visibilidad})")
        
        ventana_progreso = self._crear_ventana_progreso(
            "🌐 Creando repositorio en GitHub...",
            "Esto puede tomar unos segundos...\n(Inicializando repo, commit inicial, creando en GitHub)"
        )
        
        def crear_repo():
            try:
                resultado = self.proyecto.crear_repo_gh(nombre, visibilidad)
                self.root.after(0, lambda: self._procesar_resultado_repo(resultado, ventana_progreso, nombre))
            except Exception as e:
                self.root.after(0, lambda: self._manejar_error(e, ventana_progreso))
        
        threading.Thread(target=crear_repo, daemon=True).start()

    def _procesar_resultado_repo(self, resultado, ventana_progreso, nombre):
        ventana_progreso.destroy()
        
        if resultado == True:
            messagebox.showinfo("GitHub", 
                f"✅ Repositorio '{nombre}' creado y vinculado exitosamente!\n\n"
                "YA podés usar Push/Pull para sincronizar.")
            self.actualizar_rama_display()
            self.ver_archivos()
        else:
            messagebox.showerror("Error GitHub", 
                f"❌ Error al crear repositorio:\n\n{resultado}\n\n"
                "Verifica:\n"
                "• GitHub CLI instalado (gh)\n"
                "• Autenticado (gh auth login)\n"
                "• Conexión a internet")

# ==================== MAIN ====================
if __name__ == "__main__":
    root = ctk.CTk()
    app = AetheryonDevCoreApp(root)
    root.mainloop()