# SimulAR

Sistema para gestión, análisis y optimización del almacenamiento de simulaciones moleculares

## ANTECEDENTES DEL PROYECTO

El trabajo experimental y computacional desarrollado en el grupo QuITEx requiere el uso intensivo de herramientas de simulación molecular como AMBER, GAMESS, Gaussian y Travis. Estas herramientas permiten estudiar sistemas complejos a nivel atómico y generan grandes volúmenes de información como resultado de cada simulación realizada.
A partir del relevamiento inicial realizado mediante entrevistas con integrantes del grupo, se identificaron diversas dificultades operativas asociadas al manejo de estas simulaciones, las cuales impactan directamente en la eficiencia del trabajo cotidiano. En particular, se observaron problemáticas vinculadas a la organización de archivos, el análisis de resultados y la gestión del almacenamiento.

En primer lugar, las simulaciones generan múltiples archivos de salida, muchos de ellos de gran tamaño, es decir, que una única corrida puede producir decenas o incluso cientos de archivos, alcanzando varios gigabytes de información. Esta situación provoca una saturación progresiva del almacenamiento disponible en los equipos del laboratorio, obligando a los investigadores a eliminar archivos de manera manual, sin contar con criterios claros sobre qué información puede descartarse sin perder valor científico.

En segundo lugar, el análisis de las simulaciones se realiza actualmente de forma manual y no estandarizada, mediante comandos específicos en herramientas como Travis, cuya interfaz resulta poco intuitiva y limitada. Esto obliga a los usuarios a interactuar principalmente a través de líneas de comando y configuraciones poco guiadas, lo que incrementa la curva de aprendizaje. Como consecuencia, el proceso requiere conocimientos técnicos avanzados, es propenso a errores humanos y dificulta la reproducibilidad de los resultados, ya que cada investigador puede aplicar procedimientos distintos para obtener métricas similares.

Asimismo, se detectó la ausencia de un sistema centralizado que permita organizar la información generada por las simulaciones. Los datos se encuentran distribuidos en distintas carpetas y equipos, sin un registro estructurado que facilite su consulta, comparación o reutilización en trabajos futuros.
Finalmente, se evidenció la falta de mecanismos de gestión del ciclo de vida de los archivos generados, particularmente en lo que respecta a la identificación de archivos redundantes o prescindibles. Esta situación incrementa la carga operativa sobre los investigadores y contribuye al uso ineficiente de los recursos disponibles.
En este contexto, surge la necesidad de desarrollar una herramienta que permita mejorar la gestión de simulaciones moleculares, automatizando el análisis de resultados, centralizando la información relevante y asistiendo en la toma de decisiones relacionadas con la optimización del almacenamiento.

## DESCRIPCIÓN DEL PROYECTO

Se propone el desarrollo de una aplicación de escritorio orientada a la gestión, análisis y optimización del almacenamiento de simulaciones moleculares, con el objetivo de abordar las problemáticas identificadas en el relevamiento inicial del grupo QuITEx.

El sistema estará enfocado en el procesamiento posterior a la ejecución de simulaciones, sin intervenir en la etapa de configuración o ejecución de las mismas. Su propósito es asistir a los investigadores en la organización de archivos, el análisis de resultados y la toma de decisiones relacionadas con la gestión del almacenamiento. A tal efecto se propone la siguiente arquitectura (Figura 1) para solucionar la problemática descripta.

Figura 1: Arquitectura general del sistema propuesto para la gestión, análisis y optimización del almacenamiento de simulaciones moleculares.

### Descripción general del sistema

La solución propuesta consiste en una aplicación de escritorio desarrollada en Python, que integra funcionalidades de análisis de simulaciones, almacenamiento estructurado de resultados y asistencia en la limpieza de archivos. Además todos los datos procesados por el sistema se almacenan en una base de datos local que actúa como repositorio centralizado de las simulaciones analizadas. Esta base permite consultar métricas de simulaciones previas, acceder a información estructurada sobre archivos y resultados y facilitar la organización y trazabilidad de los experimentos realizados.

El sistema se organiza en tres componentes principales:

- Módulo de gestión de simulaciones: permite escanear directorios del sistema de archivos para identificar simulaciones existentes, registrar su estructura y almacenar metadata relevante como rutas, tamaños y tipos de archivos asociados.

- Módulo de análisis de resultados: automatiza el cálculo de métricas clave a partir de los archivos generados por las simulaciones, tales como RMSD, radio de giro y otras magnitudes relevantes. Estos resultados se almacenan de forma estructurada en una base de datos, facilitando su consulta y reutilización.
- Módulo de optimización de almacenamiento: analiza los archivos asociados a cada simulación con el fin de identificar aquellos que pueden ser eliminados sin comprometer la información relevante previamente procesada. El sistema genera recomendaciones de limpieza junto con una estimación del espacio que podría liberarse, manteniendo siempre la decisión final en manos del usuario.

El usuario interactúa con el sistema a través de una interfaz gráfica de escritorio, que permite visualizar simulaciones detectadas, ejecutar análisis, consultar métricas y gestionar la eliminación de archivos de manera controlada.

### 1. Módulo de gestión de simulaciones

Este módulo permitirá escanear directorios del sistema de archivos para identificar simulaciones existentes, registrar su estructura y almacenar metadata relevante como rutas, tamaños y tipos de archivos asociados.

### 2. Módulo de análisis y estandarización de resultados

Este módulo aborda la problemática del análisis manual y no estandarizado. A partir de los archivos de salida de las simulaciones, el sistema ejecuta un pipeline automatizado que procesa los datos de trayectoria y otros outputs relevantes mediante librerías especializadas, calcula métricas clave de forma consistente para todas las simulaciones y almacena los resultados en una base de datos estructurada, asegurando su trazabilidad y reproducibilidad.

De esta manera, se reduce la dependencia de comandos específicos y se facilita la comparación entre distintas corridas.

### 3. Módulo de gestión y optimización del almacenamiento

Este módulo se enfoca en la problemática de la saturación del almacenamiento. A partir del análisis de los archivos asociados a cada simulación, el sistema identifica archivos de gran tamaño y bajo valor analítico, detecta información redundante o ya procesada y genera recomendaciones de eliminación junto con una estimación del espacio liberable.

El sistema no elimina archivos automáticamente, sino que proporciona información clara para que el investigador pueda tomar decisiones informadas, reduciendo el riesgo de pérdida de datos relevantes.

A los efectos de esta práctica supervisada, se desarrollarán los módulos 1 y 2, enfocados en la gestión de simulaciones y en los procesos de análisis y estandarización de las mismas.

## OBJETIVOS DEL PROYECTO

- Estandarizar el análisis de simulaciones mediante la implementación de un pipeline automatizado que calcule métricas clave (como RMSD y radio de giro).
- Centralizar la información de las simulaciones en una base de datos que registre metadata, métricas y referencias a archivos.
- Implementar consultas organizadas  para seguimiento de la trazabilidad de los experimentos.
- Evaluar la organización y la accesibilidad de la aplicación los datos y resultados obtenidos de la aplicación mediante simulaciones realizadas en el laboratorio.
