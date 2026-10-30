DECLARE fecha_proceso DATE DEFAULT CURRENT_DATE() - 1;

CREATE TEMP TABLE pendientes AS
SELECT t.id_conversacion, t.fecha, t.transcripcion
FROM `mi-proyecto.call_center.transcripciones` AS t
LEFT JOIN `mi-proyecto.call_center.conversaciones_llm` AS p
       ON p.id_conversacion = t.id_conversacion
WHERE t.fecha = fecha_proceso
  AND p.id_conversacion IS NULL;

INSERT INTO `mi-proyecto.call_center.conversaciones_llm`
  (id_conversacion, fecha, documento, telefono, direccion, resumen, venta_concretada, estado_llm, fecha_carga)
SELECT
  id_conversacion,
  fecha,
  r.documento,
  r.telefono,
  r.direccion,
  r.resumen,
  r.venta_concretada,
  r.status AS estado_llm,
  CURRENT_TIMESTAMP() AS fecha_carga
FROM (
  SELECT
    id_conversacion,
    fecha,
    AI.GENERATE(
      CONCAT(
        'Sos un analista de calidad de un call center. A partir de la transcripción, ',
        'extraé: documento del cliente (solo números), teléfono de contacto, ',
        'dirección de instalación en MAYÚSCULAS, un resumen de una oración y si la venta ',
        'quedó concretada. Si un dato no aparece, devolvé NULL. No inventes datos.\n\n',
        'Transcripción:\n', transcripcion
      ),
      endpoint      => 'gemini-2.5-flash',
      output_schema => 'documento STRING, telefono STRING, direccion STRING, resumen STRING, venta_concretada BOOL'
    ) AS r
  FROM pendientes
);

SELECT COUNT(*) AS errores_llm
FROM `mi-proyecto.call_center.conversaciones_llm`
WHERE fecha = fecha_proceso
  AND estado_llm != '';
