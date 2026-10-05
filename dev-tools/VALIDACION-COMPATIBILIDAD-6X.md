# Compatibilidad dnd5e 6.x — 1.0.1

Fecha: 2026-10-05.

## Cambios y pruebas

Se conservan el formato de los avances y los datos mecánicos. Las pruebas portables comparan arrays y objetos indexados, ausencia de traducción, copia independiente y rechazo de cambios mecánicos. Los contenedores serializados con `contents` se incluyen cuando el conversor los admite.

## Comprobación en Foundry

Instancia local: Foundry 14.368, dnd5e 6.0.5 y Babele 2.9.1. Se importó directamente el conversor del módulo mediante una macro y se aplicó sobre los avances de un documento real: Bárbaro (SRD), procedente de `dnd5e.classes24`.

Resultado: PASS para array y objeto indexado. Solo cambiaron la etiqueta y la pista; niveles, configuración y valores conservaron su contenido y el origen no se modificó, incluso con campos mecánicos introducidos en el parche de prueba.

## Límites

El módulo de traducción estaba inactivo y su compendio de producto no estaba disponible en el mundo. Esta comprobación verifica el conversor con las utilidades reales de Foundry, pero no valida el registro completo en Babele ni la presentación visual del compendio correspondiente. No se ha repetido esta prueba en dnd5e 6.0.3. No constituye una revisión lingüística ni funcional exhaustiva.
