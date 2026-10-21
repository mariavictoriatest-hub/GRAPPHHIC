---
workflow: general-video
flow: automation
storyboard: yes
message: "Los registros te acompañan por el camino: llegas de una manera y te vas aliviada"
destination: instagram-reels
aspect: 1080x1920
language: es
length: 30s
angle: audio-driven stop-motion collage
---

## Intent

Motion graphic de "¿Qué son los registros?" para @abuchaljacoach, hecho SOLO con el
audio del reel original (sin la imagen de Elena). Se construye como un stop motion
de recortes reales: papel, letras de nota de rescate, luna, mariposa, libros, reloj de
arena, estrellas, flores secas y periódico, en semitono, siguiendo la estética de la
marca.

## Assets

- assets/reel.mp4 — reel original; solo se usa su audio (extraído a assets/voice.m4a).
- assets/transcript-segments.json — transcripción por frases (es), marca los tiempos de las palabras clave.
- assets/cutouts/*.png — recortes tomados de la referencia gráfica de la marca enviada por la usuaria (luna, mariposa, libro abierto, pila de libros, reloj de arena, letras S y C, flores con periódico, estrella), re-tramados en semitono a alta resolución.

## Customizations

- Colores de marca: #fff6d2, #5e3c79, #f7dbff y blanco.
- Tipografía: Noto Serif Display Extra Condensed (instancias estáticas wdth 62.5 en assets/fonts).
- Stop motion a 12 fps con "boil" (temblor de recorte) cada 2 cuadros.
- Texto: solo palabras clave impresas en tiras de papel recortado, sincronizadas con la voz.

## Notes

- Revisión con storyboard antes de animar el detalle (elección de la usuaria).
- Sin acceso a bancos de imágenes en este entorno: los recortes salen de la referencia de la marca.
