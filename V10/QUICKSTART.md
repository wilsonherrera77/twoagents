# QUICKSTART - Discovery Motor V10

**⏱️ Tiempo estimado:** 5 minutos
**Dificultad:** ⭐ Principiante

---

## 🚀 INICIO RÁPIDO (3 PASOS)

### Paso 1: Abrir la carpeta V10

```bash
cd V10
```

### Paso 2: Ejecutar el launcher

```batch
cd launchers
LAUNCH_V10_CUSTOM.bat
```

### Paso 3: Ingresar tu objetivo

```
Tu objetivo (en ingles): Create a REST API with JWT authentication
Nombre del proyecto (opcional, Enter para auto): [Enter]
```

**¡Listo!** El sistema generará tu proyecto en 1-2 segundos.

---

## 📂 ENCONTRAR TU PROYECTO

El proyecto generado estará en:

```
../workspace/tu_proyecto_nombre/
```

Por ejemplo:
```
workspace/
└── rest_api_jwt_demo/
    ├── src/
    │   ├── api_main.py
    │   ├── routes.py
    │   ├── models.py
    │   └── ...
    ├── tests/
    ├── README.md
    └── requirements.txt
```

---

## 📊 VER RESULTADOS

### Abrir el README del proyecto:

```bash
cd ../workspace/tu_proyecto/
cat README.md
```

### Ver el reporte de calidad:

```bash
cd ../reports/
ls -lt v10_async_*.json | head -1
cat [archivo_mas_reciente].json
```

**Ejemplo de reporte:**
```json
{
  "objective": "Create a REST API with JWT authentication",
  "security_score": 10.0,
  "qa_score": 5.5,
  "combined_score": 7.75,
  "decision": "NEEDS_IMPROVEMENT"
}
```

---

## ⚙️ OPCIONES AVANZADAS

### Opción 1: Launcher con objetivo predefinido

```batch
cd launchers
LAUNCH_V10_DUAL_CLAUDE.bat
```

Ejecuta un proyecto de ejemplo de microservicios.

### Opción 2: Ejecución manual (Python)

```bash
# Terminal 1: PM Agent
cd core
python claude_pm_agent.py

# Terminal 2: Orchestrator
python orchestrator_v10_async.py "Create a web scraper" --name scraper_demo
```

### Opción 3: Monitoreo en tiempo real

```batch
cd launchers
MONITOR_V10.bat
```

Actualiza cada 3 segundos mostrando:
- Procesos activos
- Mensajes en cola
- Proyectos generados
- Reportes recientes

---

## 🔍 ENTENDER LOS RESULTADOS

### Scores de Calidad:

| Score | Significado | Qué hacer |
|-------|-------------|-----------|
| **Security: 10.0** | ✅ Perfecto | Nada, está seguro |
| **QA: 5.5** | ⚠️ Mejorable | Implementar TODOs |
| **Combined: 7.75** | ⚠️ Necesita mejoras | Ver decisión |

### Decisiones del Sistema:

- **SUCCESS**: Proyecto aprobado (score >= 7.0 en ambos)
- **NEEDS_IMPROVEMENT**: Funcional pero requiere trabajo
- **FAILED**: Error crítico

---

## 🛠️ IMPLEMENTAR EL CÓDIGO

Los proyectos generados son **esqueletos funcionales**, no código completo.

### Qué está incluido:

✅ Estructura de directorios
✅ Archivos de configuración
✅ README con instrucciones
✅ Tests esqueleto
✅ requirements.txt

### Qué necesitas hacer:

❌ Implementar lógica de negocio
❌ Completar tests funcionales
❌ Agregar manejo de errores
❌ Configurar base de datos

### Ejemplo:

**Código generado:**
```python
class UserAuth:
    def authenticate(self, username: str, password: str) -> bool:
        # TODO: Implement authentication logic
        pass
```

**Tu implementación:**
```python
class UserAuth:
    def authenticate(self, username: str, password: str) -> bool:
        user = db.query(User).filter_by(username=username).first()
        if user and bcrypt.verify(password, user.password_hash):
            return True
        return False
```

---

## 🐛 SOLUCIÓN DE PROBLEMAS

### Problema: "No se abre ninguna ventana"

**Solución:**
Verifica que estás en la carpeta correcta:
```bash
pwd  # Debe mostrar: .../V10/launchers
```

### Problema: "Python no encontrado"

**Solución:**
Verifica tu instalación de Python:
```bash
python --version  # Debe ser 3.11+
```

Si no funciona:
```bash
py --version  # Prueba con 'py' en lugar de 'python'
```

### Problema: "El proyecto está vacío"

**Solución:**
Revisa el reporte JSON para ver si hubo errores:
```bash
cd ../reports
cat v10_async_[timestamp].json
```

Busca el campo `"status"` y `"error"` si existe.

### Problema: "Score QA muy bajo (< 5.0)"

**Solución:**
Esto es **normal y esperado**. El sistema genera esqueletos.
El QA score mejorará cuando implementes los TODOs.

---

## 📚 SIGUIENTES PASOS

### 1. Lee la documentación completa:

```bash
cd ../docs
cat README_V10_INNOVACION.md
```

### 2. Explora ejemplos de proyectos:

```bash
cd ../examples/projects
ls -la
```

### 3. Revisa la historia de versiones:

```bash
cd ../docs
cat VERSION_HISTORY.md
```

### 4. Personaliza tu proyecto:

```bash
cd ../workspace/tu_proyecto
# Edita los archivos .py para implementar tu lógica
```

---

## 💡 TIPS ÚTILES

### Tip 1: Usa objetivos específicos

**❌ Malo:**
```
"Create an API"
```

**✅ Bueno:**
```
"Create a REST API with JWT authentication, PostgreSQL database, and CRUD operations for users"
```

### Tip 2: Revisa siempre el README generado

El README del proyecto incluye:
- Setup instructions
- Estructura del proyecto
- Tecnologías usadas
- Próximos pasos

### Tip 3: Los scores bajos son esperados

V10 genera **esqueletos funcionales**, no productos finales.
Un score de 7.75 significa: "estructura buena, implementa la lógica".

### Tip 4: Usa el monitor para debugging

Si algo falla, `MONITOR_V10.bat` muestra en tiempo real:
- Qué procesos están corriendo
- Qué mensajes se están enviando
- Dónde están los logs

---

## 🎓 RECURSOS ADICIONALES

- **README principal**: `../README.md`
- **Documentación técnica**: `../docs/README_V10_INNOVACION.md`
- **Historia completa**: `../docs/VERSION_HISTORY.md`
- **Ejemplos**: `../examples/`

---

## 🎉 ¡ÉXITO!

Si llegaste hasta aquí y generaste tu primer proyecto, **¡felicidades!**

Discovery Motor V10 acaba de crear tu estructura de proyecto en ~1 segundo,
algo que en V5-V9 tomaba 2.5 horas y fallaba 100% del tiempo.

**Próximo paso:** Implementa la lógica de negocio en tu proyecto generado.

---

**Versión:** 1.0.0
**Última actualización:** 22 de Octubre de 2025
