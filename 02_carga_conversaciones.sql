TRUNCATE TABLE dbo.stg_conversaciones_llm;

BULK INSERT dbo.stg_conversaciones_llm
FROM 'D:\cargas\carga_conversaciones.csv'
WITH (
    FIRSTROW        = 2,
    FIELDTERMINATOR = '|',
    ROWTERMINATOR   = '0x0d0a',
    CODEPAGE        = '1252',
    TABLOCK
);

INSERT INTO dbo.conversaciones_llm_facts
    (id_conversacion, fecha, hash_conversacion, documento, telefono, direccion,
     resumen, venta_concretada, requiere_revision, transcripcion_gz)
SELECT s.id_conversacion, s.fecha, s.hash_conversacion, s.documento, s.telefono, s.direccion,
       s.resumen, s.venta_concretada, s.requiere_revision, s.transcripcion_gz
FROM dbo.stg_conversaciones_llm AS s
WHERE NOT EXISTS (
    SELECT 1
    FROM dbo.conversaciones_llm_facts AS f
    WHERE f.hash_conversacion = s.hash_conversacion
);

SELECT
    COUNT(*) AS filas_stg,
    SUM(CASE WHEN requiere_revision = 1 THEN 1 ELSE 0 END) AS filas_a_revisar
FROM dbo.stg_conversaciones_llm;
