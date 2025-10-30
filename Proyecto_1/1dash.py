import streamlit as st
import pandas as pd
import os
from datetime import datetime
import numpy as np
import json
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io

# Configuración de la página
st.set_page_config(
    page_title="Gestor de CSV - Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Carpeta donde están los CSV
CARPETA = r"C:\\BELTRAN\\Ciencia\\MINERIA\\TP1"

def listar_csv():
    """Listar todos los archivos CSV disponibles"""
    try:
        archivos = [f for f in os.listdir(CARPETA) if f.endswith(".csv")]
        return archivos
    except FileNotFoundError:
        st.error(f"❌ No se encontró la carpeta: {CARPETA}")
        return []

def cargar_datos(archivo):
    """Cargar datos desde CSV"""
    ruta = os.path.join(CARPETA, archivo)
    try:
        df = pd.read_csv(ruta)
        return df, ruta
    except Exception as e:
        st.error(f"Error al cargar el archivo: {e}")
        return pd.DataFrame(), ruta

def guardar_datos(df, ruta):
    """Guardar DataFrame en archivo CSV"""
    try:
        df.to_csv(ruta, index=False)
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        return False

def detectar_columna_id(df):
    """Detectar automáticamente la columna que funciona como ID"""
    if df.empty:
        return None
    
    # Patrones comunes para columnas de ID
    patrones_id = [
        'id', 'ID', 'Id', 'codigo', 'cod', 'codigo', 'numero', 'nro', 
        'clave', 'key', 'identificador'
    ]
    
    # Buscar en nombres de columnas
    for col in df.columns:
        col_lower = col.lower()
        
        # Verificar si el nombre de la columna contiene algún patrón de ID
        for patron in patrones_id:
            if patron in col_lower:
                return col
        
        # Verificar si la columna tiene valores únicos y secuenciales (como un ID)
        if (df[col].dtype in ['int64', 'float64'] and 
            len(df[col].unique()) == len(df)):
            # Verificar si es secuencial (aproximadamente)
            valores_ordenados = sorted(df[col].unique())
            if len(valores_ordenados) > 1:
                diferencias = [valores_ordenados[i+1] - valores_ordenados[i] for i in range(len(valores_ordenados)-1)]
                if all(diff == 1 for diff in diferencias):
                    return col
    
    # Si no encuentra, usar la primera columna numérica
    columnas_numericas = df.select_dtypes(include=['int64', 'float64']).columns
    if len(columnas_numericas) > 0:
        return columnas_numericas[0]
    
    return None

def obtener_siguiente_id(df, columna_id):
    """Obtener el siguiente ID automáticamente"""
    if df.empty or columna_id is None:
        return 1
    
    if columna_id in df.columns:
        try:
            # Convertir a numérico y ignorar valores no numéricos
            ids_numericos = pd.to_numeric(df[columna_id], errors='coerce')
            ids_numericos = ids_numericos.dropna()
            
            if len(ids_numericos) > 0:
                siguiente = int(ids_numericos.max()) + 1
            else:
                siguiente = len(df) + 1
        except:
            siguiente = len(df) + 1
    else:
        siguiente = len(df) + 1
    
    return siguiente

def generar_graficos(df):
    """Generar gráficos estadísticos basados en los datos"""
    graficos = []
    
    # Identificar columnas numéricas y categóricas
    columnas_numericas = df.select_dtypes(include=[np.number]).columns.tolist()
    columnas_categoricas = df.select_dtypes(include=['object']).columns.tolist()
    
    # Gráfico 1: Distribución de variables numéricas
    if len(columnas_numericas) > 0:
        for col in columnas_numericas[:3]:  # Máximo 3 columnas numéricas
            try:
                fig = px.histogram(df, x=col, title=f'Distribución de {col}', 
                                 template='plotly_white')
                fig.update_layout(height=400)
                graficos.append((f"hist_{col}", fig))
            except Exception as e:
                st.warning(f"No se pudo generar histograma para {col}: {e}")
    
    # Gráfico 2: Boxplot para variables numéricas
    if len(columnas_numericas) > 0:
        try:
            fig = px.box(df, y=columnas_numericas[:3], 
                        title='Diagrama de Caja - Variables Numéricas',
                        template='plotly_white')
            fig.update_layout(height=400)
            graficos.append(("boxplot", fig))
        except Exception as e:
            st.warning(f"No se pudo generar boxplot: {e}")
    
    # Gráfico 3: Conteo de categorías
    if len(columnas_categoricas) > 0:
        for col in columnas_categoricas[:2]:  # Máximo 2 columnas categóricas
            try:
                counts = df[col].value_counts().head(10)  # Top 10 categorías
                fig = px.bar(x=counts.index, y=counts.values, 
                           title=f'Top 10 - {col}',
                           labels={'x': col, 'y': 'Count'},
                           template='plotly_white')
                fig.update_layout(height=400)
                graficos.append((f"bar_{col}", fig))
            except Exception as e:
                st.warning(f"No se pudo generar gráfico de barras para {col}: {e}")
    
    # Gráfico 4: Correlación entre variables numéricas
    if len(columnas_numericas) >= 2:
        try:
            corr_matrix = df[columnas_numericas].corr()
            fig = px.imshow(corr_matrix, 
                          title='Matriz de Correlación',
                          color_continuous_scale='RdBu_r',
                          aspect="auto",
                          template='plotly_white')
            fig.update_layout(height=500)
            graficos.append(("correlation", fig))
        except Exception as e:
            st.warning(f"No se pudo generar matriz de correlación: {e}")
    
    # Gráfico 5: Scatter plot si hay al menos 2 variables numéricas
    if len(columnas_numericas) >= 2:
        try:
            fig = px.scatter(df, x=columnas_numericas[0], y=columnas_numericas[1],
                           title=f'Relación entre {columnas_numericas[0]} y {columnas_numericas[1]}',
                           template='plotly_white')
            fig.update_layout(height=400)
            graficos.append(("scatter", fig))
        except Exception as e:
            st.warning(f"No se pudo generar scatter plot: {e}")
    
    # Gráfico 6: Series temporales si existe columna de fecha
    columnas_fecha = [col for col in df.columns if 'fecha' in col.lower() or 'date' in col.lower() or 'time' in col.lower()]
    if len(columnas_fecha) > 0 and len(columnas_numericas) > 0:
        try:
            fecha_col = columnas_fecha[0]
            # Intentar convertir a datetime
            df_temp = df.copy()
            df_temp[fecha_col] = pd.to_datetime(df_temp[fecha_col], errors='coerce')
            df_temp = df_temp.dropna(subset=[fecha_col])
            
            if len(df_temp) > 0:
                fig = px.line(df_temp, x=fecha_col, y=columnas_numericas[0],
                            title=f'Evolución Temporal - {columnas_numericas[0]}',
                            template='plotly_white')
                fig.update_layout(height=400)
                graficos.append(("time_series", fig))
        except Exception as e:
            st.warning(f"No se pudo generar serie temporal: {e}")
    
    return graficos

def main():
    # Título principal
    st.title("Gestor de Archivos CSV ")
    st.markdown("---")
    
    # Sidebar para navegación
    st.sidebar.title(" Navegación")
    
    # Listar archivos CSV
    archivos = listar_csv()
    
    if not archivos:
        st.error("No se encontraron archivos CSV en la carpeta especificada.")
        return
    
    # Selección de archivo en sidebar
    archivo_seleccionado = st.sidebar.selectbox(
        "Selecciona un archivo CSV:",
        archivos,
        key="archivo_selector"
    )
    
    # Cargar datos del archivo seleccionado
    if archivo_seleccionado:
        df, ruta = cargar_datos(archivo_seleccionado)
        
        # Mostrar información del archivo
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(" Archivo", archivo_seleccionado)
        with col2:
            st.metric(" Registros", len(df))
        with col3:
            st.metric(" Columnas", len(df.columns))
        with col4:
            memoria = df.memory_usage(deep=True).sum() / 1024**2
            st.metric(" Memoria", f"{memoria:.2f} MB")
        
        st.markdown("---")
        
        # Tabs para diferentes funcionalidades - AGREGAMOS NUEVAS PESTAÑAS
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "📋 Ver Datos", 
            "➕ Insertar", 
            "✏️ Modificar", 
            "🗑️ Eliminar", 
            "🔍 Buscar",
            "📊 Gráficos",  # NUEVA PESTAÑA
            "💾 Exportar"   # NUEVA PESTAÑA
        ])
        
        # Tab 1: Ver Datos
        with tab1:
            st.header("Visualización de Datos")
            
            if not df.empty:
                # Mostrar todos los datos
                st.dataframe(df, use_container_width=True)
                
                
            else:
                st.info("El archivo está vacío. Usa la pestaña 'Insertar' para agregar datos.")
        
        # Tab 2: Insertar Registro - MEJORADO CON ID AUTOMÁTICO
        with tab2:
            st.header("Insertar Nuevo Registro")
            
            if df.empty:
                st.warning("No se pueden insertar registros porque no hay columnas definidas.")
            else:
                # Detectar columna de ID y siguiente ID disponible
                columna_id = detectar_columna_id(df)
                siguiente_id = obtener_siguiente_id(df, columna_id)
                
                st.write("**Columnas disponibles:**", list(df.columns))
                
                if columna_id:
                   # st.success(f"🎯 **Columna de ID detectada:** `{columna_id}`")
                    st.info(f"🆔 **El siguiente ID disponible es:** `{siguiente_id}`")
                
                # Formulario para insertar nuevo registro
                with st.form("form_insertar"):
                    nuevo_registro = {}
                    cols = st.columns(2)  # Dividir en 2 columnas para mejor visualización
                    
                    for i, col in enumerate(df.columns):
                        with cols[i % 2]:  # Alternar entre columnas
                            # Si es la columna de ID, mostrar información especial
                            if col == columna_id:
                                st.markdown(f"**{col}** 🆔")
                                st.caption(f"Siguiente ID: {siguiente_id}")
                                valor = st.text_input(
                                    f"Valor para {col}",
                                    value=str(siguiente_id),
                                    key=f"insert_{col}",
                                    help=f"ID automático sugerido: {siguiente_id}. Puedes cambiarlo si es necesario."
                                )
                            else:
                                valor = st.text_input(f"{col}", key=f"insert_{col}")
                            
                            nuevo_registro[col] = valor
                    
                    submitted = st.form_submit_button("💾 Insertar Registro")
                    
                    if submitted:
                        # Validar que no haya campos vacíos
                        campos_vacios = [col for col, valor in nuevo_registro.items() if valor == ""]
                        
                        if campos_vacios:
                            st.error(f"Los siguientes campos están vacíos: {', '.join(campos_vacios)}")
                        else:
                            # Validar ID único si es columna de ID
                            if columna_id and columna_id in nuevo_registro:
                                try:
                                    id_ingresado = int(nuevo_registro[columna_id])
                                    # Verificar si el ID ya existe
                                    if columna_id in df.columns:
                                        ids_existentes = pd.to_numeric(df[columna_id], errors='coerce').dropna()
                                        if id_ingresado in ids_existentes.values:
                                            st.error(f"❌ El ID {id_ingresado} ya existe en la base de datos.")
                                            st.info(f"💡 El siguiente ID disponible es: {siguiente_id}")
                                            st.stop()
                                    
                                    # Advertencia si el ID no es secuencial
                                    if id_ingresado != siguiente_id:
                                        st.warning(f"⚠️ El ID ingresado ({id_ingresado}) no es secuencial. El siguiente ID sería: {siguiente_id}")
                                        if not st.checkbox("✅ Confirmar que deseo usar este ID no secuencial"):
                                            st.stop()
                                
                                except ValueError:
                                    st.error(f"❌ El valor para {columna_id} debe ser un número entero.")
                                    st.stop()
                            
                            # Convertir tipos de datos
                            registro_convertido = {}
                            for col, valor in nuevo_registro.items():
                                if df[col].dtype in ['int64', 'float64']:
                                    try:
                                        if '.' in valor:
                                            registro_convertido[col] = float(valor)
                                        else:
                                            registro_convertido[col] = int(valor)
                                    except ValueError:
                                        registro_convertido[col] = valor
                                else:
                                    registro_convertido[col] = valor
                            
                            # Agregar el nuevo registro
                            nuevo_df = pd.DataFrame([registro_convertido])
                            df = pd.concat([df, nuevo_df], ignore_index=True)
                            
                            # Guardar automáticamente
                            if guardar_datos(df, ruta):
                                st.success(" ✅ Registro insertado y guardado exitosamente!")
                                st.balloons()
                                st.rerun()
                            else:
                                st.error(" ❌ Error al guardar el registro")
        
        # Tab 3: Modificar Registro
        with tab3:
            st.header("Modificar Registro Existente")
            
            if df.empty:
                st.info("No hay registros para modificar.")
            else:
                # Seleccionar registro a modificar
                indice_modificar = st.selectbox(
                    "Selecciona el índice del registro a modificar:",
                    range(len(df)),
                    format_func=lambda x: f"Registro {x}: {dict(df.iloc[x])}"
                )
                
                if st.button("Cargar Registro para Modificar"):
                    registro_actual = df.iloc[indice_modificar]
                    st.session_state.registro_modificar = registro_actual.copy()
                    st.session_state.indice_modificar = indice_modificar
                
                if 'registro_modificar' in st.session_state:
                    st.subheader("Modificando Registro:")
                    st.write(st.session_state.registro_modificar)
                    
                    with st.form("form_modificar"):
                        registro_modificado = {}
                        cols = st.columns(2)
                        
                        for i, col in enumerate(df.columns):
                            with cols[i % 2]:
                                valor_actual = st.session_state.registro_modificar[col]
                                nuevo_valor = st.text_input(
                                    f"{col}", 
                                    value=str(valor_actual),
                                    key=f"mod_{col}"
                                )
                                registro_modificado[col] = nuevo_valor
                        
                        submitted = st.form_submit_button(" 💾 Guardar Cambios")
                        
                        if submitted:
                            # Aplicar cambios
                            for col, valor in registro_modificado.items():
                                if valor != str(st.session_state.registro_modificar[col]):
                                    # Convertir tipo de dato si es necesario
                                    if df[col].dtype in ['int64', 'float64']:
                                        try:
                                            if '.' in valor:
                                                df.at[st.session_state.indice_modificar, col] = float(valor)
                                            else:
                                                df.at[st.session_state.indice_modificar, col] = int(valor)
                                        except ValueError:
                                            df.at[st.session_state.indice_modificar, col] = valor
                                    else:
                                        df.at[st.session_state.indice_modificar, col] = valor
                            
                            # Guardar cambios
                            if guardar_datos(df, ruta):
                                st.success(" ✅ Registro modificado exitosamente!")
                                del st.session_state.registro_modificar
                                del st.session_state.indice_modificar
                                st.rerun()
                            else:
                                st.error(" ❌ Error al guardar los cambios")
        
        # Tab 4: Eliminar Registro - SOLUCIÓN DEFINITIVA
        with tab4:
            st.header("🗑️ Eliminar Registros")
            
            if df.empty:
                st.info("No hay registros para eliminar.")
            else:
                # Usar multiselect para selección simple
                opciones = [f"Registro {i}: {', '.join([f'{k}={v}' for k, v in df.iloc[i].items()])}" for i in range(len(df))]
                
                seleccion = st.multiselect(
                    "Selecciona los registros a eliminar:",
                    options=range(len(df)),
                    format_func=lambda x: f"Registro {x}: {', '.join([f'{k}={v}' for k, v in df.iloc[x].items()])}"
                )
                
                if seleccion:
                    st.subheader("📋 Registros seleccionados para eliminar:")
                    st.dataframe(df.iloc[seleccion], use_container_width=True)
                    
                    st.warning(f"⚠️ Se eliminarán {len(seleccion)} registro(s). Esta acción no se puede deshacer.")
                    
                    if st.button("🗑️ CONFIRMAR ELIMINACIÓN", type="primary"):
                        # ELIMINAR Y ACTUALIZAR
                        try:
                            # Crear copia del DataFrame sin los registros seleccionados
                            df_nuevo = df.drop(seleccion).reset_index(drop=True)
                            
                            # Guardar en el archivo
                            exito = guardar_datos(df_nuevo, ruta)
                            
                            if exito:
                                st.success(f" ✅ {len(seleccion)} registro(s) eliminado(s) exitosamente!")
                                
                                # ACTUALIZAR EL DATAFRAME GLOBAL - ESTO ES CLAVE
                                # Necesitamos forzar la recarga del archivo
                                df, ruta = cargar_datos(archivo_seleccionado)
                                
                                st.info(" Datos actualizados correctamente")
                                st.rerun()
                            else:
                                st.error(" ❌ Error al guardar los cambios")
                                
                        except Exception as e:
                            st.error(f" ❌ Error: {e}")
                else:
                    st.info(" Selecciona registros de la lista para eliminarlos")
        
        # Tab 5: Buscar Registros
        with tab5:
            st.header("Buscar Registros")
            
            if df.empty:
                st.info("No hay registros para buscar.")
            else:
                col_busqueda, valor_busqueda = st.columns(2)
                
                with col_busqueda:
                    columna_buscar = st.selectbox(
                        "Columna para buscar:",
                        df.columns
                    )
                
                with valor_busqueda:
                    valor_buscar = st.text_input("Valor a buscar:")
                
                if valor_buscar:
                    # Realizar búsqueda
                    try:
                        if df[columna_buscar].dtype in ['int64', 'float64']:
                            # Búsqueda numérica
                            if '.' in valor_buscar:
                                valor_buscar = float(valor_buscar)
                            else:
                                valor_buscar = int(valor_buscar)
                            resultados = df[df[columna_buscar] == valor_buscar]
                        else:
                            # Búsqueda textual
                            resultados = df[df[columna_buscar].astype(str).str.contains(valor_buscar, case=False)]
                    except ValueError:
                        # Si falla la conversión, buscar como texto
                        resultados = df[df[columna_buscar].astype(str).str.contains(valor_buscar, case=False)]
                    
                    if len(resultados) > 0:
                        st.success(f" ✅ Se encontraron {len(resultados)} registros:")
                        st.dataframe(resultados, use_container_width=True)
                    else:
                        st.info("No se encontraron registros que coincidan con la búsqueda.")
        
        # NUEVA TAB 6: GRÁFICOS ESTADÍSTICOS
        with tab6:
            st.header("📊 Análisis Gráfico y Estadístico")
            
            if df.empty:
                st.info("No hay datos para generar gráficos.")
            else:
                # Selector de tipo de gráfico
                st.subheader("Configuración de Gráficos")
                
                # Generar gráficos automáticamente
                st.subheader("Gráficos Automáticos")
                graficos = generar_graficos(df)
                
                if graficos:
                    for nombre, fig in graficos:
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No se pudieron generar gráficos automáticamente con los datos disponibles.")
                
               
        
        # NUEVA TAB 7: EXPORTAR DATOS
        with tab7:
            st.header("💾 Exportar Datos")
            
            if df.empty:
                st.info("No hay datos para exportar.")
            else:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Exportar Formato CSV")
                    nombre_csv = st.text_input("Nombre del archivo CSV:", 
                                             value=f"{archivo_seleccionado.split('.')[0]}_export.csv")
                    
                    csv_data = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Descargar CSV",
                        data=csv_data,
                        file_name=nombre_csv,
                        mime="text/csv",
                        key="download_csv"
                    )
                
                with col2:
                    st.subheader("Exportar Formato JSON")
                    nombre_json = st.text_input("Nombre del archivo JSON:", 
                                              value=f"{archivo_seleccionado.split('.')[0]}_export.json")
                    
                    # Opciones de formato JSON
                    formato_json = st.radio("Formato JSON:", 
                                          ["Records", "Split", "Values"], 
                                          help="Records: lista de objetos, Split: separado en índices y datos, Values: solo valores")
                    
                    if formato_json == "Records":
                        json_data = df.to_json(orient='records', indent=2)
                    elif formato_json == "Split":
                        json_data = df.to_json(orient='split', indent=2)
                    else:
                        json_data = df.to_json(orient='values', indent=2)
                    
                    st.download_button(
                        label="📥 Descargar JSON",
                        data=json_data,
                        file_name=nombre_json,
                        mime="application/json",
                        key="download_json"
                    )
                
                st.markdown("---")
                
                # Exportación avanzada
                st.subheader("Opciones Avanzadas de Exportación")
                
                col3, col4 = st.columns(2)
                
                with col3:
                    st.subheader("Exportar a Excel")
                    nombre_excel = st.text_input("Nombre del archivo Excel:", 
                                               value=f"{archivo_seleccionado.split('.')[0]}_export.xlsx")
                    
                    # Crear archivo Excel en memoria
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                        df.to_excel(writer, sheet_name='Datos', index=False)
                        
                        # Agregar hoja con estadísticas si hay columnas numéricas
                        columnas_numericas = df.select_dtypes(include=[np.number]).columns
                        if len(columnas_numericas) > 0:
                            df[columnas_numericas].describe().to_excel(writer, sheet_name='Estadísticas')
                    
                    excel_data = excel_buffer.getvalue()
                    
                    st.download_button(
                        label="📥 Descargar Excel",
                        data=excel_data,
                        file_name=nombre_excel,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_excel"
                    )
                
                with col4:
                    st.subheader("Exportar Datos Filtrados")
                    st.info("Selecciona columnas específicas para exportar:")
                    
                    columnas_exportar = st.multiselect(
                        "Selecciona columnas:",
                        df.columns.tolist(),
                        default=df.columns.tolist()
                    )
                    
                    if columnas_exportar:
                        df_filtrado = df[columnas_exportar]
                        
                        formato_filtrado = st.selectbox("Formato para datos filtrados:", 
                                                      ["CSV", "JSON"])
                        
                        nombre_filtrado = st.text_input("Nombre archivo filtrado:",
                                                      value=f"{archivo_seleccionado.split('.')[0]}_filtrado.{formato_filtrado.lower()}")
                        
                        if formato_filtrado == "CSV":
                            data_filtrado = df_filtrado.to_csv(index=False)
                            mime_type = "text/csv"
                        else:
                            data_filtrado = df_filtrado.to_json(orient='records', indent=2)
                            mime_type = "application/json"
                        
                        st.download_button(
                            label=f"📥 Descargar {formato_filtrado} Filtrado",
                            data=data_filtrado,
                            file_name=nombre_filtrado,
                            mime=mime_type,
                            key="download_filtered"
                        )
        
        
        
        # Información adicional en sidebar
        st.sidebar.markdown("---")
        st.sidebar.header("ℹ Información")
        st.sidebar.write(f"**Carpeta:** {CARPETA}")
        st.sidebar.write(f"**Última actualización:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Estadísticas rápidas en sidebar
        if not df.empty:
            st.sidebar.markdown("---")
            st.sidebar.header("📊 Resumen")
            st.sidebar.write(f"**Registros:** {len(df)}")
            st.sidebar.write(f"**Columnas:** {len(df.columns)}")
            
            columnas_numericas = df.select_dtypes(include=[np.number]).columns
            if len(columnas_numericas) > 0:
                st.sidebar.write(f"**Columnas numéricas:** {len(columnas_numericas)}")
            
            nulos = df.isnull().sum().sum()
            if nulos > 0:
                st.sidebar.warning(f"**Valores nulos:** {nulos}")

if __name__ == "__main__":
    main()