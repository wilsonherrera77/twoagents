# Autonomous Development Team System

Sistema completo de desarrollo autónomo con agentes IA especializados que colaboran para crear proyectos de software funcionales de forma completamente automatizada.

## 🎯 Descripción General

Este sistema implementa un **equipo autónomo de desarrollo** compuesto por:
- **PM_Agent**: Project Manager que planifica, supervisa y valida
- **Dev_Agent**: Developer que implementa, programa y ejecuta
- **Message Broker**: Sistema de comunicación con protocolo estricto v1.0

Los agentes colaboran siguiendo un protocolo riguroso para generar proyectos reales con archivos funcionales, tests y documentación.

## ✅ Estado Actual - Completamente Funcional

### Características Implementadas
- ✅ **Sistema de comunicación robusto** con protocolo v1.0/v2.0
- ✅ **Interfaz web** (Flask) en `http://localhost:5000`
- ✅ **CLI completo** con comandos especializados
- ✅ **Selector de carpeta de destino** (gráfico y por parámetro)
- ✅ **Generación de archivos reales** (no simulación)
- ✅ **Tests automáticos** incluidos en cada proyecto
- ✅ **Soporte Unicode completo** (903+ caracteres corregidos)
- ✅ **Autonomía configurable** (low/medium/high)
- ✅ **Protocolo estricto** con fases definidas

### Errores Resueltos
- ✅ UnicodeEncodeError completamente eliminado
- ✅ Comunicación entre agentes validada
- ✅ Generación real de archivos funcionando
- ✅ Interfaz web estable sin crashes
- ✅ CLI operativo con todos los comandos

## 🚀 Inicio Rápido

### Prerrequisitos
```bash
Python 3.8+
Flask
click
tkinter (para selector gráfico)
```

### Instalación
```bash
git clone https://github.com/wilsonherrera77/motor_final
cd motor_final
pip install flask click
```

### Uso

#### 1. Interfaz Web (Recomendado)
```bash
python web_interface.py
# Abrir http://localhost:5000
```

#### 2. CLI - Ejecución Directa
```bash
# Con selector gráfico de carpeta
python autonomous_cli.py execute --objective "Crear una calculadora" --select-directory

# Especificando directorio
python autonomous_cli.py execute --objective "API REST para usuarios" --output-dir "C:/MisProyectos"

# Con comunicación visible
python autonomous_cli.py execute --objective "Juego Snake" --show-communication
```

#### 3. Demostración
```bash
python autonomous_cli.py demo
```

## 📁 Estructura del Proyecto

```
discovery_motor_final/
├── autonomous_team_system.py     # Sistema principal de orquestación
├── developer_agent.py           # Agente desarrollador con políticas
├── project_manager_agent.py     # Agente PM con validaciones
├── web_interface.py             # Interfaz web Flask
├── autonomous_cli.py            # CLI con comandos
├── message_contracts_v2.py      # Contratos de comunicación
├── global_system_prompt.py      # Prompts globales v1.0
├── agent_communication.py       # MessageBroker y routing
├── role_assignment.py           # Asignación dinámica de roles
├── fix_unicode_aggressive.py    # Script de reparación Unicode
└── generated_projects/          # Proyectos creados por el sistema
```

## 🛠 Arquitectura Técnica

### Protocolo de Comunicación v1.0
```json
{
  "schema_version": "1.0",
  "from": "PM_Agent",
  "to": "Dev_Agent",
  "message_type": "task_spec",
  "correlation_id": "TASK-001",
  "payload": {
    "title": "Implementar funcionalidad X",
    "acceptance_criteria": ["Criterio 1", "Criterio 2"]
  }
}
```

### Fases de Ejecución
1. **Bootstrap**: Handshake inicial entre agentes
2. **Planning**: PM envía especificaciones, Dev genera plan técnico
3. **Execution**: Desarrollo iterativo con progreso reportado
4. **Validation**: QA y tests automáticos
5. **Closure**: Entrega final y reporte

### Tipos de Mensaje Soportados
- `question`/`answer`: Bootstrap inicial
- `task_spec`: Especificaciones de PM a Dev
- `ack`: Confirmaciones de recepción
- `implementation_plan`: Plan técnico detallado
- `approval_response`: Aprobación/rechazo de PM
- `implementation_progress`: Updates de progreso
- `implementation_completed`: Notificación de completitud
- `finish`: Cierre de proyecto

## 🧠 Para Sistemas IA y Desarrolladores

### Extender el Sistema

#### Agregar Nuevo Tipo de Agente
```python
# En autonomous_team_system.py
class NewAgent:
    def __init__(self, name, autonomy_level="medium"):
        self.name = name
        self.autonomy_level = autonomy_level

    def handle_message(self, message):
        # Implementar lógica específica
        pass
```

#### Agregar Nuevo Tipo de Mensaje
```python
# En message_contracts_v2.py
MESSAGE_TYPES = {
    # Existentes...
    "new_message_type": {
        "description": "Descripción del mensaje",
        "payload_schema": {
            "required_field": "string",
            "optional_field": "optional"
        }
    }
}
```

#### Personalizar Prompts
```python
# En global_system_prompt.py
def get_custom_task_spec(objective):
    if "machine_learning" in objective.lower():
        return {
            "title": f"ML Implementation: {objective}",
            "acceptance_criteria": [
                "Modelo entrenado y evaluado",
                "Pipeline de datos implementado",
                "Métricas de performance documentadas"
            ]
        }
```

### Niveles de Autonomía
- **low**: PM aprueba cada paso, intervención manual
- **medium**: PM supervisa, Dev ejecuta con autonomía limitada
- **high**: Ejecución completamente autónoma con mínima supervisión

### Hooks de Extensión
```python
# Pre-execution hook
def before_project_start(objective, workspace):
    # Lógica personalizada antes del inicio
    pass

# Post-execution hook
def after_project_complete(workspace, files_created):
    # Lógica personalizada después del completado
    pass
```

## 📊 Casos de Uso Probados

### Exitosos ✅
- ✅ **Videojuego Snake**: Pygame con movimiento, comida, puntuación
- ✅ **Calculadora simple**: Interfaz con operaciones básicas
- ✅ **API REST**: Endpoints CRUD con Flask
- ✅ **Archivo "Hola Mundo"**: Proyecto simple funcional
- ✅ **Dashboard web**: HTML/CSS/JS interactivo

### Estructura de Salida Típica
```
proyecto_generado_YYYYMMDD_HHMMSS/
├── main.py                # Archivo principal ejecutable
├── config.json           # Metadatos del proyecto
├── README.md             # Documentación
├── tests/
│   └── test_main.py      # Tests unitarios
└── requirements.txt      # Dependencias (si aplica)
```

## 🔧 Comandos CLI Disponibles

```bash
# Ver status del sistema
python autonomous_cli.py status

# Limpiar workspace
python autonomous_cli.py cleanup

# Analizar reporte específico
python autonomous_cli.py analyze --report-id "REPORT_123"

# Ejecución con monitoreo
python autonomous_cli.py execute \
  --objective "Crear dashboard de ventas" \
  --output-dir "C:/Proyectos" \
  --monitor-interval 5 \
  --export-report \
  --show-communication
```

## 🌐 API de la Interfaz Web

### Endpoints Principales
- `GET /`: Interfaz principal de desarrollo
- `POST /execute`: Ejecutar objetivo con agentes
- `GET /projects`: Listar proyectos creados
- `GET /browse/<path>`: Explorador de archivos
- `POST /select-directory`: Selector de carpeta
- `GET /status`: Estado del sistema

### Ejemplo de Uso Programático
```python
import requests

response = requests.post('http://localhost:5000/execute', json={
    'objective': 'Crear sistema de inventario',
    'autonomy_level': 'medium',
    'output_directory': '/ruta/destino'
})

project_info = response.json()
print(f"Proyecto creado en: {project_info['workspace']}")
```

## 🐛 Debugging y Logs

### Logs del Sistema
```bash
# Ver comunicación entre agentes
python autonomous_cli.py execute --objective "..." --show-communication

# Modo debug en web
DEBUG=true python web_interface.py
```

### Archivos de Log
- `autonomous_workspace/reports/`: Reportes de ejecución
- `dev_workspace/`: Workspace temporal del desarrollador
- Console output: Comunicación en tiempo real

## 🔮 Roadmap para Extensiones

### Corto Plazo
- [ ] Soporte para múltiples lenguajes (Node.js, Java, C#)
- [ ] Integración con Git automática
- [ ] Templates de proyecto personalizables
- [ ] Sistema de plugins

### Mediano Plazo
- [ ] Agente de QA especializado
- [ ] Agente de DevOps para deployment
- [ ] Integración con APIs externas
- [ ] Dashboard de métricas avanzado

### Largo Plazo
- [ ] Red de agentes especializados
- [ ] Aprendizaje automático de patrones
- [ ] Integración con IDEs
- [ ] Marketplace de agentes

## 🤝 Contribución

### Para Desarrolladores
1. Fork del repositorio
2. Crear rama feature: `git checkout -b feature/nueva-funcionalidad`
3. Asegurar que tests pasen: `python -m pytest`
4. Enviar PR con descripción detallada

### Para Sistemas IA
1. Extender `global_system_prompt.py` para nuevos dominios
2. Agregar nuevos tipos de mensaje en `message_contracts_v2.py`
3. Implementar agentes especializados heredando de base classes
4. Probar con `autonomous_cli.py demo`

## 📝 Licencia

MIT License - Ver LICENSE file para detalles

## 📞 Soporte

- **Issues**: GitHub Issues para bugs y feature requests
- **Documentación**: Wiki del repositorio
- **Ejemplos**: Directorio `examples/` con casos de uso

---

## 🎉 Reconocimientos

Sistema desarrollado y validado completamente funcional con:
- **903+ caracteres Unicode corregidos**
- **Protocolo de comunicación robusto**
- **Generación real de archivos funcionales**
- **Interfaces múltiples (Web + CLI)**
- **Tests automáticos incluidos**

**¡Listo para producción y extensión por equipos de desarrollo!**