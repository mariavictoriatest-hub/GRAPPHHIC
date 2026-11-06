# Portfolio · María Victoria

Portfolio web de una sola página, estilo collage/scrapbook: cielo y pasto, estampillas con borde perforado, estrellas cromadas, cintas, clips, notas de papel, marquesinas y mockups de redes.
Es **universal** (no está dirigido a ninguna marca) y apunta a roles de Marketing Manager, Social Media Manager y Paid Media.
**Todos los casos, métricas y testimonios son ficticios**: reemplazalos por los reales.

## Estructura
1. Portada (estampilla con nombre, roles y paleta)
2. Sobre mí (carpeta con foto, experiencia, herramientas, educación, idiomas)
3. En números
4. Índice
5. 01/ Estrategia & Marketing: caso Aula Nova
6. 02/ Redes sociales: caso Raíz Café
7. 03/ Paid Media: caso Bloom Cosmética
8. Cómo trabajo · Testimonios · Contacto

## Editar textos sin código
1. Abrí `index.html` en el navegador.
2. Tocá el botón ✎ (abajo a la derecha) o presioná **E**.
3. Hacé clic en cualquier texto marcado y escribí.
4. **Descargar HTML** guarda una copia con tus cambios.

Las estrellas cromadas se pueden arrastrar (doble clic las devuelve a su lugar).

## Foto
Guardá tu foto como `img/maria-victoria.jpg` y reemplazá el texto `MV` dentro de `.photo-card .ph` por:
`<img src="img/maria-victoria.jpg" alt="María Victoria">`

## Cielo con foto real (opcional)
El cielo y el pasto están hechos con CSS. Para usar una foto, en la regla `.sky` del `<style>` reemplazá el `background` por `url("img/cielo.jpg") center/cover`.

## Gráficos
Los valores del gráfico de ROAS se cambian en `data-bars="1.4,2.1,..."` y `data-max`.

## Tipografías de marca
Anantason Expand, Garet y Rocking Horse no están en Google Fonts. Si están instaladas en tu computadora se usan solas; para que se vean en cualquier equipo, copiá los archivos a `fonts/`:
- `fonts/AnantasonExpand.woff2` (u `.otf`)
- `fonts/Garet-Book.woff2` y `fonts/Garet-Heavy.woff2`
- `fonts/RockingHorse.woff2`

Mientras tanto se usan: Archivo, Manrope y Fraunces Italic (más Special Elite para la nota de herramientas y Caveat para lo manuscrito).

## Publicarlo
Es un archivo HTML estático: se puede subir a GitHub Pages, Netlify o Vercel tal cual.
