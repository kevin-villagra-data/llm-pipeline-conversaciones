IF OBJECT_ID('dbo.stg_conversaciones_llm') IS NOT NULL DROP TABLE dbo.stg_conversaciones_llm;
CREATE TABLE dbo.stg_conversaciones_llm (
    id_conversacion   VARCHAR(20)   NOT NULL,
    fecha             DATE          NOT NULL,
    hash_conversacion CHAR(64)      NOT NULL,
    documento         VARCHAR(15)   NULL,
    telefono          VARCHAR(20)   NULL,
    direccion         VARCHAR(200)  NULL,
    resumen           VARCHAR(500)  NULL,
    venta_concretada  BIT           NULL,
    requiere_revision BIT           NOT NULL,
    transcripcion_gz  VARCHAR(MAX)  NULL
);

IF OBJECT_ID('dbo.conversaciones_llm_facts') IS NULL
CREATE TABLE dbo.conversaciones_llm_facts (
    id_conversacion   VARCHAR(20)   NOT NULL,
    fecha             DATE          NOT NULL,
    hash_conversacion CHAR(64)      NOT NULL,
    documento         VARCHAR(15)   NULL,
    telefono          VARCHAR(20)   NULL,
    direccion         VARCHAR(200)  NULL,
    resumen           VARCHAR(500)  NULL,
    venta_concretada  BIT           NULL,
    requiere_revision BIT           NOT NULL,
    transcripcion_gz  VARCHAR(MAX)  NULL,
    fecha_carga       DATETIME2(0)  NOT NULL CONSTRAINT df_conv_llm_fecha_carga DEFAULT SYSDATETIME(),
    CONSTRAINT pk_conversaciones_llm_facts PRIMARY KEY CLUSTERED (hash_conversacion)
);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'ix_conv_llm_fecha')
CREATE NONCLUSTERED INDEX ix_conv_llm_fecha
    ON dbo.conversaciones_llm_facts (fecha)
    INCLUDE (documento, venta_concretada, requiere_revision);
