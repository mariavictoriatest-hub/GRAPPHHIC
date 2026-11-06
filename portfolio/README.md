# Portfolio interactivo · María Victoria

Presentación HTML de 12 diapositivas para enviar a clientes o reclutadores (Marketing Manager · Social Media Manager · Paid Media).
**Todos los datos son ficticios**: hay que reemplazarlos por casos y métricas reales.

## Cómo abrirla
Abrí `index.html` en el navegador. Funciona sin instalar nada.

## Personalizar por cliente (sin tocar código)
Agregá parámetros a la URL:

```
index.html?cliente=Acme%20Corp&rol=Paid%20Media
```

- `cliente` aparece arriba a la derecha, en "Cómo puedo ayudar a…" y en el cierre.
- `rol` deja abierta esa tarjeta en la diapositiva de roles (`Marketing Manager`, `Social Media Manager` o `Paid Media`).

También podés cambiar los valores por defecto `CLIENTE` y `ROL_DESTACADO` al principio del `<script>`.

## Editar textos sin código
1. Presioná **E**: los textos editables quedan marcados con línea punteada.
2. Hacé clic y escribí.
3. Tocá **Descargar HTML editado**: se guarda `portfolio-<cliente>.html`, listo para enviar.

## Atajos
| Tecla | Acción |
|---|---|
| ← → / espacio | Navegar |
| O | Índice de diapositivas |
| F | Pantalla completa |
| E | Modo edición |
| #5 al final de la URL | Abre la diapositiva 5 |

En móvil se navega deslizando.

## Exportar a PDF
Ctrl/Cmd + P → "Guardar como PDF". Cada diapositiva sale en una página.

## Tipografías de marca
Anantason Expand, Garet y Rocking Horse no están en Google Fonts. Si están instaladas en tu computadora se usan solas. Para que se vean en cualquier equipo, copiá los archivos en `fonts/` con estos nombres:

- `fonts/AnantasonExpand.woff2` (u `.otf`)
- `fonts/Garet-Book.woff2` y `fonts/Garet-Heavy.woff2`
- `fonts/RockingHorse.woff2`

Mientras tanto se usan alternativas parecidas: Archivo Expanded, Manrope y Fraunces Italic.

## Foto
Guardá tu foto como `img/maria-victoria.jpg` y descomentá la línea `<img …>` dentro de `.photo` en la portada.

## Gráficos
Los valores de las barras se cambian en el atributo `data-bars` de cada caso, por ejemplo `data-bars="1.4,2.1,2.9"` y `data-max="6"`.
