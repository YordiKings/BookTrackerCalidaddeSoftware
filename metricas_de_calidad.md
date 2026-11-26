# Métricas de calidad de BookTracker

Este archivo conserva los datos que alimentaban el **Dashboard de métricas ágiles** (`books/data/metrics.json`), que se retiró del proyecto. Los datos pertenecen al **Milestone 1** de **BookTracker 1.0**, con corte al **2026-10-09**.

**Equipo:** Jorge Reyes Rojas, Rafael Isaac Gómez Ortega, Sergio Alexis Lamas Bravo.

---

## 1. Datos por sprint

Cada sprint duró una semana (lunes a viernes).

| Sprint | Inicio | Fin | SP comprometidos | SP completados | Predictibilidad | Velocidad (SP) | Lead time (días) | Cobertura | Defectos | Densidad de defectos | CSAT | Horas |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Sprint 01 | 2026-09-07 | 2026-09-11 | 10 | 10 | 100.0 % | 10 | 2.5 | 10 % | 0 | 0.0 | N/D | 12 |
| Sprint 02 | 2026-09-14 | 2026-09-18 | 15 | 5 | 33.3 % | 5 | 6.0 | 25 % | 0 | 0.0 | N/D | 6 |
| Sprint 03 | 2026-09-21 | 2026-09-25 | 15 | 8 | 53.3 % | 8 | 5.5 | 45 % | 0 | 0.0 | N/D | 6 |
| Sprint 04 | 2026-09-28 | 2026-10-02 | 20 | 20 | 100.0 % | 20 | 3.0 | 70 % | 0 | 0.0 | N/D | 26 |
| Sprint 05 | 2026-10-05 | 2026-10-09 | 25 | 25 | 100.0 % | 25 | 2.5 | 90 % | 0 | 0.0 | N/D | 36 |

## 2. Resumen global (KPIs)

| KPI | Valor |
|---|---|
| Story Points completados en total | 68 |
| Velocidad media | 13.6 SP por sprint |
| Predictibilidad media | 77.3 % |
| Lead time medio | 3.9 días |
| Densidad de defectos | 0.0 defectos por SP |
| Cobertura de código final | 90 % |
| CSAT | N/D (sin datos) |
| Horas totales invertidas | 86 h |

---

## 3. Qué significa cada métrica

### Story Points (SP) comprometidos y completados
- **Qué son:** los Story Points son una unidad relativa para estimar el esfuerzo de una tarea. Dependen de su complejidad, incertidumbre y volumen de trabajo, no de las horas.
- **Comprometidos (`committed_sp`):** los SP que el equipo se propuso terminar al inicio del sprint.
- **Completados (`completed_sp`):** los SP de las tareas que realmente quedaron terminadas al cierre del sprint.

### Predictibilidad (`predictability_pct`)
- **Qué mide:** qué tan bien cumple el equipo lo que promete.
- **Fórmula:** `SP completados ÷ SP comprometidos × 100`.
- **Lectura:** 100 % significa que se cumplió todo lo comprometido. Un valor bajo indica que se subestimó el trabajo o hubo imprevistos.
- **En los datos:** el Sprint 02 (33.3 %, 5 de 15 SP) y el Sprint 03 (53.3 %, 8 de 15 SP) fueron los más débiles. Los sprints 01, 04 y 05 cumplieron el 100 %.

### Velocidad (`velocity_sp`)
- **Qué mide:** cuánto trabajo termina el equipo por sprint, en SP completados.
- **Para qué sirve:** planear sprints futuros y ver la tendencia de productividad.
- **En los datos:** subió de 10 a 5, 8, 20 y 25 SP. El equipo se estabilizó y aceleró hacia el final del milestone. La media fue de 13.6 SP por sprint.

### Lead time (`lead_time_days`)
- **Qué mide:** los días que pasan desde que se solicita una tarea hasta que se entrega.
- **Lectura:** menos es mejor, porque el flujo de trabajo es más ágil.
- **En los datos:** el pico fue de 6.0 días en el Sprint 02 y bajó a 2.5 días en el Sprint 05. La media fue de 3.9 días.

### Cobertura de código (`code_coverage_pct`)
- **Qué mide:** el porcentaje del código ejecutable que es recorrido por las pruebas automáticas.
- **Para qué sirve:** es un indicador de qué tan protegido está el código contra regresiones. No garantiza que las pruebas sean buenas, solo que el código se ejecuta al probarlo.
- **En los datos:** creció sprint a sprint, de 10 % a 25 %, 45 %, 70 % y 90 %. Ese 90 % es el valor final del milestone.

### Defectos encontrados (`defects_found`)
- **Qué mide:** el número de bugs detectados durante el sprint.
- **En los datos:** 0 en todos los sprints.

### Densidad de defectos (`defect_density_sp`)
- **Qué mide:** cuántos defectos hay por unidad de trabajo entregado.
- **Fórmula:** `defectos encontrados ÷ SP completados`.
- **Lectura:** menos es mejor. Normaliza los defectos por el tamaño del trabajo, así que permite comparar sprints grandes y pequeños.
- **En los datos:** 0.0 en todos los sprints.

### CSAT (`csat_score`)
- **Qué mide:** *Customer Satisfaction*, el porcentaje de respuestas satisfechas en las encuestas a clientes o usuarios.
- **En los datos:** sin valor (`null`, N/D). El dashboard lo dejaba como un módulo pendiente para futuras versiones.

### Horas invertidas (`hours_spent`)
- **Qué mide:** el tiempo real dedicado al sprint, sumado entre todos los integrantes.
- **Para qué sirve:** contrastar el esfuerzo real con los SP completados.
- **En los datos:** el total fue de 86 h. Los dos últimos sprints concentraron 62 h (26 y 36).

---

## 4. Datos originales (JSON)

```json
{
  "project": "BOOKTRACKER",
  "version": "1.0",
  "as_of_date": "2026-10-09",
  "milestone": "Milestone 1",
  "team_members": [
    "Jorge Reyes Rojas",
    "Rafael Isaac Gómez Ortega",
    "Sergio Alexis Lamas Bravo"
  ],
  "sprints": [
    {
      "sprint_name": "Sprint 01",
      "start_date": "2026-09-07",
      "end_date": "2026-09-11",
      "committed_sp": 10,
      "completed_sp": 10,
      "predictability_pct": 100.0,
      "velocity_sp": 10,
      "lead_time_days": 2.5,
      "code_coverage_pct": 10.0,
      "defects_found": 0,
      "defect_density_sp": 0.0,
      "csat_score": null,
      "hours_spent": 12.0
    },
    {
      "sprint_name": "Sprint 02",
      "start_date": "2026-09-14",
      "end_date": "2026-09-18",
      "committed_sp": 15,
      "completed_sp": 5,
      "predictability_pct": 33.3,
      "velocity_sp": 5,
      "lead_time_days": 6.0,
      "code_coverage_pct": 25.0,
      "defects_found": 0,
      "defect_density_sp": 0.0,
      "csat_score": null,
      "hours_spent": 6.0
    },
    {
      "sprint_name": "Sprint 03",
      "start_date": "2026-09-21",
      "end_date": "2026-09-25",
      "committed_sp": 15,
      "completed_sp": 8,
      "predictability_pct": 53.3,
      "velocity_sp": 8,
      "lead_time_days": 5.5,
      "code_coverage_pct": 45.0,
      "defects_found": 0,
      "defect_density_sp": 0.0,
      "csat_score": null,
      "hours_spent": 6.0
    },
    {
      "sprint_name": "Sprint 04",
      "start_date": "2026-09-28",
      "end_date": "2026-10-02",
      "committed_sp": 20,
      "completed_sp": 20,
      "predictability_pct": 100.0,
      "velocity_sp": 20,
      "lead_time_days": 3.0,
      "code_coverage_pct": 70.0,
      "defects_found": 0,
      "defect_density_sp": 0.0,
      "csat_score": null,
      "hours_spent": 26.0
    },
    {
      "sprint_name": "Sprint 05",
      "start_date": "2026-10-05",
      "end_date": "2026-10-09",
      "committed_sp": 25,
      "completed_sp": 25,
      "predictability_pct": 100.0,
      "velocity_sp": 25,
      "lead_time_days": 2.5,
      "code_coverage_pct": 90.0,
      "defects_found": 0,
      "defect_density_sp": 0.0,
      "csat_score": null,
      "hours_spent": 36.0
    }
  ],
  "kpis_summary": {
    "total_sp_completed": 68,
    "avg_velocity_sp": 13.6,
    "avg_predictability_pct": 77.3,
    "avg_lead_time_days": 3.9,
    "defect_density_per_sp": 0.0,
    "final_code_coverage_pct": 90.0,
    "csat_score": null,
    "total_hours_spent": 86.0
  }
}
```
