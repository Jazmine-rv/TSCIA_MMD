import pandas as pd
import os
from datetime import datetime

# Carpeta donde están los CSV
CARPETA = r"C:\\BELTRAN\\Ciencia\\MINERIA\\TP1"

def listar_csv():
    #Listar todos los archivos CSV disponibles
    archivos = [f for f in os.listdir(CARPETA) if f.endswith(".csv")]
    return archivos

def cargar_datos(archivo):
    #Cargar datos desde CSV o crear DataFrame vacío si no existe
    ruta = os.path.join(CARPETA, archivo)
    try:
        df = pd.read_csv(ruta)
        print(f" Archivo '{archivo}' cargado con éxito ({len(df)} registros)")
        return df, ruta
    except FileNotFoundError:
        print(f" El archivo '{archivo}' no existe, se creará uno nuevo al guardar.")
        return pd.DataFrame(), ruta
    except Exception as e:
        print(f" Error al cargar el archivo: {e}")
        return pd.DataFrame(), ruta

def guardar_datos(df, ruta):
    #Guardar DataFrame en archivo CSV
    try:
        df.to_csv(ruta, index=False)
        print(f" Cambios guardados en '{os.path.basename(ruta)}'")
        return True
    except Exception as e:
        print(f" Error al guardar: {e}")
        return False

def detectar_columna_id(df):
   #Detectar automáticamente la columna que funciona como ID
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
            df[col].is_monotonic_increasing and 
            len(df[col].unique()) == len(df)):
            return col
    
    # Si no encuentra, usar la primera columna numérica
    columnas_numericas = df.select_dtypes(include=['int64', 'float64']).columns
    if len(columnas_numericas) > 0:
        return columnas_numericas[0]
    
    # Si no hay columnas numéricas, usar la primera columna
    return df.columns[0] if len(df.columns) > 0 else None

def obtener_siguiente_id(df, columna_id):
    #Obtener el siguiente ID automáticamente
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

def mostrar_datos(df, limite=None):
    #Mostrar datos del DataFrame - SIEMPRE muestra todos
    if df.empty:
        print(" No hay datos cargados.")
        return
    
    print(f"\n{'_'*60}")
    print(f" DATOS ACTUALES ({len(df)} registros)")
    print(f"{'_'*60}")
    
    # SIEMPRE mostrar todos los registros
    print(df)
    
    # Mostrar información adicional
    print(f"\n Total de registros: {len(df)}")

def insertar_registro(df):
    #Insertar un nuevo registro con validación y ID automático
    if df.empty:
        print(" No se puede insertar porque no hay columnas definidas en el CSV.")
        return df, False
    
    print(f"\n INSERTAR NUEVO REGISTRO")
    print(f" Columnas: {list(df.columns)}")
    print(" Escriba 'atras' en cualquier momento para volver al menú anterior")
    
    # Detectar columna de ID automáticamente
    columna_id = detectar_columna_id(df)
    siguiente_id = obtener_siguiente_id(df, columna_id)
    
    if columna_id:
       # print(f"\n  COLUMNA DE ID DETECTADA: '{columna_id}'")
        print(f"  EL SIGUIENTE ID DISPONIBLE ES: {siguiente_id}")
    
    nuevo = {}
    for col in df.columns:
        while True:
            # Si es columna de ID, manejar de forma especial
            if col == columna_id:
                print(f"\n  Ingresando valor para '{col}':")
                print(f"    El siguiente ID disponible es: {siguiente_id}")
                
                valor_input = input(f"    Ingrese valor (Enter para usar {siguiente_id}): ").strip()
                
                # Opción para volver al menú anterior
                if valor_input.lower() == 'atras':
                    print(" Volviendo al menú anterior...")
                    return df, True
                
                # Si presiona Enter, usar el ID automático
                if valor_input == "":
                    valor = siguiente_id
                    print(f"     Se usará ID automático: {valor}")
                else:
                    valor = valor_input
                    
                    # Validar que el ID no exista
                    if col in df.columns:
                        try:
                            # Intentar convertir a numérico para comparar
                            valor_num = pd.to_numeric(valor, errors='coerce')
                            if not pd.isna(valor_num):
                                valores_existentes = pd.to_numeric(df[col], errors='coerce')
                                if valor_num in valores_existentes.values:
                                    print(f"     ERROR: El {col} '{valor}' ya existe")
                                    print(f"     El siguiente ID disponible es: {siguiente_id}")
                                    continue
                        except:
                            # Si falla la conversión, verificar como string
                            if str(valor) in df[col].astype(str).values:
                                print(f"     ERROR: El {col} '{valor}' ya existe")
                                print(f"     El siguiente ID disponible es: {siguiente_id}")
                                continue
                    
                    # Validar que sea el ID correcto
                    try:
                        valor_num = int(valor)
                        if valor_num != siguiente_id:
                            print(f"      ADVERTENCIA: El ID secuencial correcto sería {siguiente_id}")
                            confirmar = input(f"    ¿Está seguro de usar {valor_num}? (s/n): ").lower()
                            if confirmar != 's':
                                continue
                    except ValueError:
                        print("     El ID debe ser un número entero")
                        continue
                        
            else:
                # Para columnas que no son ID
                valor = input(f" Ingrese valor para '{col}': ").strip()
            
            # Opción para volver al menú anterior (para columnas no ID)
            if col != columna_id and str(valor).lower() == 'atras':
                print(" Volviendo al menú anterior...")
                return df, True
            
            if valor == "":
                print(" Este campo no puede estar vacío. Intente nuevamente.")
                continue
            
            # Validar tipos de datos basados en datos existentes
            if not df.empty and df[col].dtype in ['int64', 'float64']:
                try:
                    if '.' in str(valor):
                        valor = float(valor)
                    else:
                        valor = int(valor)
                except ValueError:
                    print(f" '{col}' requiere un valor numérico. Intente nuevamente.")
                    continue
            
            nuevo[col] = valor
            break
    
    # Agregar el nuevo registro
    nuevo_df = pd.DataFrame([nuevo])
    df = pd.concat([df, nuevo_df], ignore_index=True)
    print("  Registro insertado exitosamente")
    return df, False

def modificar_registro(df):
    #Modificar registro existente con mejoras
    if df.empty:
        print(" No hay registros para modificar.")
        return df, False
    
    mostrar_datos(df)
    print(" Escriba 'atras' en cualquier momento para volver al menú anterior")
    
    try:
        indice_input = input(f"\n Ingrese el índice (fila) a modificar (0-{len(df)-1}): ").strip()
        
        # Opción para volver al menú anterior
        if indice_input.lower() == 'atras':
            print(" Volviendo al menú anterior...")
            return df, True
        
        indice = int(indice_input)
        
        if 0 <= indice < len(df):
            print(f"\n Modificando registro {indice}:")
            print(df.iloc[indice])
            
            for col in df.columns:
                actual = df.at[indice, col]
                nuevo = input(f" {col} [actual: {actual}]: ").strip()
                
                # Opción para volver al menú anterior
                if nuevo.lower() == 'atras':
                    print(" Volviendo al menú anterior...")
                    return df, True
                
                if nuevo != "":
                    # Validar tipo de dato
                    if df[col].dtype in ['int64', 'float64']:
                        try:
                            if '.' in nuevo:
                                nuevo = float(nuevo)
                            else:
                                nuevo = int(nuevo)
                        except ValueError:
                            print(f" Valor no válido para '{col}'. Se mantiene el valor actual.")
                            continue
                    
                    df.at[indice, col] = nuevo
            
            print("  Registro modificado exitosamente")
        else:
            print("  Índice fuera de rango.")
    except ValueError:
        print("  Debe ingresar un número válido.")
    
    return df, False

def eliminar_registro(df):
    #Eliminar registro con confirmación
    if df.empty:
        print(" No hay registros para eliminar.")
        return df, False
    
    mostrar_datos(df)
    print(" Escriba 'atras' en cualquier momento para volver al menú anterior")
    
    try:
        indice_input = input(f"\n Ingrese el índice (fila) a eliminar (0-{len(df)-1}): ").strip()
        
        # Opción para volver al menú anterior
        if indice_input.lower() == 'atras':
            print(" Volviendo al menú anterior...")
            return df, True
        
        indice = int(indice_input)
        
        if 0 <= indice < len(df):
            print(f"\n REGISTRO A ELIMINAR:")
            print(df.iloc[indice])
            
            confirmar = input(" ¿Está seguro de eliminar este registro? (s/n/atras): ").lower()
            
            if confirmar == 'atras':
                print(" Volviendo al menú anterior...")
                return df, True
            elif confirmar == 's':
                df = df.drop(indice).reset_index(drop=True)
                print("  Registro eliminado exitosamente")
            else:
                print("  Eliminación cancelada")
        else:
            print("  Índice fuera de rango.")
    except ValueError:
        print("  Debe ingresar un número válido.")
    
    return df, False

def buscar_registros(df):
    #Buscar registros por criterios
    if df.empty:
        print(" No hay registros para buscar.")
        return
    
    print(f"\n  BUSCAR REGISTROS")
    print(f" Columnas disponibles: {list(df.columns)}")
    print(" Escriba 'atras' en cualquier momento para volver al menú anterior")
    
    columna = input(" Ingrese la columna para buscar: ").strip()
    
    # Opción para volver al menú anterior
    if columna.lower() == 'atras':
        print(" Volviendo al menú anterior...")
        return
    
    if columna not in df.columns:
        print("  Columna no válida.")
        return
    
    valor_buscar = input(f" Ingrese el valor a buscar en '{columna}': ").strip()
    
    # Opción para volver al menú anterior
    if valor_buscar.lower() == 'atras':
        print(" Volviendo al menú anterior...")
        return
    
    # Realizar búsqueda
    try:
        if df[columna].dtype in ['int64', 'float64']:
            # Búsqueda numérica
            if '.' in valor_buscar:
                valor_buscar = float(valor_buscar)
            else:
                valor_buscar = int(valor_buscar)
            resultados = df[df[columna] == valor_buscar]
        else:
            # Búsqueda textual (case insensitive)
            resultados = df[df[columna].astype(str).str.lower().str.contains(valor_buscar.lower())]
    except ValueError:
        # Si falla la conversión, buscar como texto
        resultados = df[df[columna].astype(str).str.lower().str.contains(valor_buscar.lower())]
    
    if len(resultados) > 0:
        print(f"\n  Se encontraron {len(resultados)} registros:")
        print(resultados)
    else:
        print("  No se encontraron registros que coincidan con la búsqueda.")

def seleccionar_archivo():
    #Seleccionar archivo CSV - MENÚ PRINCIPAL
    archivos = listar_csv()
    if not archivos:
        print(" No hay archivos CSV en la carpeta especificada.")
        print(f" Carpeta: {CARPETA}")
        return None
    
    while True:
        print(f"\n{'_'*50}")
        print(" GESTOR DE ARCHIVOS CSV - MENÚ PRINCIPAL ")
        print(f"{'_'*50}")
        
        print("\n Archivos CSV disponibles:")
        for i, f in enumerate(archivos, 1):
            print(f"  {i}. {f}")
        print(f"  {len(archivos) + 1}.  Salir del programa")

        try:
            opcion = input(f"\n Seleccione una opción (1-{len(archivos) + 1}): ").strip()
            
            if opcion == str(len(archivos) + 1):
                print("  ¡Adios!")
                return "salir"
            elif opcion.isdigit() and 1 <= int(opcion) <= len(archivos):
                archivo = archivos[int(opcion) - 1]
                return archivo
            else:
                print("  Opción inválida. Por favor, seleccione un número válido.")
        except ValueError:
            print("  Debe ingresar un número válido.")

def menu_archivo(archivo, df, ruta):
    #Menú para operaciones específicas del archivo
    cambios_pendientes = False
    
    while True:
        print(f"\n{'_'*50}")
        print(f"  ARCHIVO ACTUAL: {archivo}")
        print(f"  REGISTROS: {len(df)}")
        if cambios_pendientes:
            print("   Hay cambios pendientes por guardar")
        print(f"{'_'*50}")
        print("1.  Mostrar datos")
        print("2.  Insertar registro")
        print("3.  Modificar registro")
        print("4.  Eliminar registro")
        print("5.  Buscar registros")
        print("6.  Guardar cambios")
        print("7.  Guardar y volver al menú principal")
        print("8.  Volver al menú principal sin guardar")
        print("0.  Salir del programa")
        print("_"*50)

        opcion = input(" Seleccione una opción: ").strip()

        if opcion == "1":
            mostrar_datos(df)
        elif opcion == "2":
            df, cancelado = insertar_registro(df)
            if not cancelado:
                cambios_pendientes = True
        elif opcion == "3":
            df, cancelado = modificar_registro(df)
            if not cancelado:
                cambios_pendientes = True
        elif opcion == "4":
            df, cancelado = eliminar_registro(df)
            if not cancelado:
                cambios_pendientes = True
        elif opcion == "5":
            buscar_registros(df)
        elif opcion == "6":
            if guardar_datos(df, ruta):
                cambios_pendientes = False
        elif opcion == "7":
            if cambios_pendientes:
                if guardar_datos(df, ruta):
                    print("  Cambios guardados. Volviendo al menú principal...")
                else:
                    print("  No se pudieron guardar los cambios.")
            print("  Volviendo al menú principal...")
            return True  # Volver al menú principal
        elif opcion == "8":
            if cambios_pendientes:
                confirmar = input("   Hay cambios sin guardar. ¿Está seguro? (s/n): ").lower()
                if confirmar != 's':
                    continue
                print("  Los cambios no guardados se perderán.")
            print("  Volviendo al menú principal...")
            return True  # Volver al menú principal
        elif opcion == "0":
            if cambios_pendientes:
                confirmar = input("   Hay cambios sin guardar. ¿Está seguro de salir? (s/n): ").lower()
                if confirmar != 's':
                    continue
            print("  ¡Adios!")
            return False  # Salir del programa
        else:
            print("  Opción no válida. Por favor, seleccione 0-8.")

        # Pausa para continuar
        if opcion not in ["7", "8", "0"]:
            input("\n ⏎ Presione Enter para continuar...")

def main():
    #Programa principal mejorado
    print(" INICIANDO GESTOR AVANZADO DE ARCHIVOS CSV")
    
    while True:
        # MENÚ PRINCIPAL - Selección de archivos
        resultado = seleccionar_archivo()
        
        if resultado == "salir":
            break
        elif resultado is None:
            continue
        else:
            archivo = resultado
            
        # Cargar datos del archivo seleccionado
        df, ruta = cargar_datos(archivo)
        
        # MENÚ DE ARCHIVO - Operaciones específicas
        continuar = menu_archivo(archivo, df, ruta)
        if not continuar:
            break

    print("  Programa terminado")

if __name__ == "__main__":
    main()