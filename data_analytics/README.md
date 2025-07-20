# Sistema de Análisis de Datos - SoulTrack

## Descripción General

El módulo de análisis de datos proporciona un sistema completo para evaluar el rendimiento de los usuarios en hábitos y tareas, generando informes detallados y recomendaciones personalizadas.

## Funcionalidades Principales

### 1. Análisis Individual de Usuarios
- **Dashboard Principal**: Muestra métricas clave de rendimiento
- **Análisis Avanzado**: Incluye tendencias y recomendaciones personalizadas
- **Análisis Individual Detallado**: Reporte completo con insights específicos

### 2. Análisis Grupal (Solo Administradores)
- **Comparación de Usuarios**: Rankings y estadísticas generales
- **Identificación de Usuarios que Necesitan Ayuda**
- **Top Usuarios por Rendimiento**

### 3. Métricas Calculadas

#### Rendimiento General
- Porcentaje de hábitos completados exitosamente
- Porcentaje de tareas completadas
- Promedio general de rendimiento

#### Análisis Temporal
- Días activo del usuario
- Racha actual de días consecutivos
- Mejor racha histórica

#### Análisis por Hábito
- Porcentaje de completado por hábito
- Tendencia (mejorando, estable, empeorando, nuevo)
- Identificación de hábitos que necesitan mejora

## Modelos de Datos

### AnalisisUsuario
Almacena el análisis de rendimiento de cada usuario:
- Métricas generales (total hábitos, tareas, etc.)
- Porcentajes de rendimiento
- Análisis temporal (días activo, rachas)
- Hábitos que necesitan mejora

### MetricaHabitual
Métricas específicas por hábito:
- Días completados vs total
- Porcentaje de completado
- Tendencia del hábito
- Recomendaciones específicas

### ReporteRendimiento
Reportes detallados de rendimiento:
- Resumen ejecutivo
- Áreas de mejora
- Logros destacados
- Recomendaciones personalizadas
- Puntuación general (1-10)

### ComparacionUsuarios
Análisis grupal de usuarios:
- Estadísticas generales
- Rankings de usuarios
- Identificación de tendencias

## URLs Disponibles

- `/data_analytics/dashboard/` - Dashboard principal
- `/data_analytics/dashboard/advanced/` - Análisis avanzado
- `/data_analytics/analisis/individual/` - Análisis individual
- `/data_analytics/comparacion/usuarios/` - Comparación de usuarios (solo admin)
- `/data_analytics/api/metricas/` - API de métricas (JSON)

## Funciones de Análisis

### actualizar_analisis_usuario(user)
Actualiza el análisis de rendimiento de un usuario:
- Calcula métricas de hábitos y tareas
- Determina porcentajes de rendimiento
- Calcula días activo y rachas
- Identifica hábitos que necesitan mejora

### generar_reporte_rendimiento(user)
Genera un reporte detallado de rendimiento:
- Crea resumen ejecutivo
- Identifica áreas de mejora
- Destaca logros
- Genera recomendaciones personalizadas

### generar_recomendaciones(user, analisis)
Genera recomendaciones basadas en el análisis:
- Recomendaciones por rendimiento de hábitos
- Sugerencias de consistencia
- Enfoque en hábitos específicos

### analizar_tendencias_usuario(user)
Analiza las tendencias del usuario:
- Compara rendimiento reciente vs histórico
- Determina si está mejorando, empeorando o estable
- Proporciona mensajes motivacionales

### generar_comparacion_usuarios()
Genera comparación entre todos los usuarios:
- Calcula estadísticas generales
- Identifica top usuarios
- Encuentra usuarios que necesitan ayuda
- Determina tendencia general

## Criterios de Evaluación

### Rendimiento de Hábitos
- **Excelente**: ≥80% de hábitos completados
- **Bueno**: 60-79% de hábitos completados
- **Necesita mejora**: <60% de hábitos completados

### Rendimiento de Tareas
- **Excelente**: ≥80% de tareas completadas
- **Bueno**: 60-79% de tareas completadas
- **Necesita mejora**: <60% de tareas completadas

### Consistencia
- **Excelente**: Racha de ≥7 días
- **Bueno**: Racha de 3-6 días
- **Necesita mejora**: Racha de <3 días

## Recomendaciones Automáticas

El sistema genera recomendaciones basadas en:
1. **Rendimiento bajo en hábitos**: Sugiere mejorar consistencia
2. **Racha corta**: Recomienda construir rachas más largas
3. **Hábitos específicos con bajo rendimiento**: Enfoque en hábitos problemáticos
4. **Tendencias negativas**: Sugerencias para revertir tendencias

## API de Métricas

Endpoint: `/data_analytics/api/metricas/`
Retorna JSON con:
- Rendimiento general y por categoría
- Días activo y rachas
- Hábitos que necesitan mejora
- Métricas por hábito individual

## Configuración de Administración

Todos los modelos están registrados en el admin de Django con:
- Filtros por fecha y rendimiento
- Búsqueda por usuario
- Campos de solo lectura para métricas calculadas
- Organización en fieldsets para mejor navegación

## Uso del Sistema

### Para Usuarios Regulares
1. Acceder al dashboard principal para ver métricas básicas
2. Usar el análisis avanzado para insights detallados
3. Revisar recomendaciones personalizadas
4. Seguir el análisis individual para reportes completos

### Para Administradores
1. Acceder a comparación de usuarios para análisis grupal
2. Revisar top usuarios y usuarios que necesitan ayuda
3. Monitorear tendencias generales del sistema
4. Gestionar datos desde el panel de administración

## Notas Técnicas

- Los análisis se actualizan automáticamente cada día
- Los reportes se generan para períodos de 30 días
- Las comparaciones de usuarios se actualizan cada 24 horas
- Todas las métricas se calculan en tiempo real
- El sistema es escalable y puede manejar múltiples usuarios

## Dependencias

- Django 3.x+
- Chart.js para gráficos
- Modelos de `activities` para datos de hábitos
- Sistema de autenticación de Django 