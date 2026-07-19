# Principios filosóficos de seguridad

Estas son las mentalidades que guían la arquitectura. Cuando dudes sobre una
decisión de diseño, vuelve a estos principios.

## Triada CIA

El objetivo de toda seguridad se resume en tres propiedades:

- **Confidencialidad** — los datos solo los ven quienes deben. Se logra con
  cifrado (en tránsito y reposo) y control de acceso.
- **Integridad** — los datos no se alteran sin autorización. Se logra con
  validación, firmas/hashes, control de versiones y permisos de escritura
  estrictos.
- **Disponibilidad** — el sistema funciona cuando se necesita. Se logra con rate
  limiting, manejo robusto de errores, redundancia y protección contra DoS
  (incluido el auto-infligido por código ineficiente).

Toda decisión de seguridad busca preservar al menos una de las tres sin romper
las otras.

## Defensa en Profundidad (Defense in Depth)

Como un castillo medieval: no confíes en una sola muralla. Si el atacante cruza
el firewall, debe toparse con autenticación fuerte; si pasa la auth, los datos
en la base deben estar cifrados; si accede a la base, los permisos deben
limitarlo. **Capas redundantes**: ninguna falla única debe comprometer todo.

## Principio del Menor Privilegio (PoLP)

Ningún usuario, servicio, token o porción de código debe tener más permisos de
los estrictamente necesarios. El servidor web no necesita permiso para borrar la
base completa; un token de lectura no debe poder escribir; un microservicio solo
accede a los recursos que usa. **Denegar por defecto**, conceder lo mínimo.

## Zero Trust (Confianza Cero)

"Nunca confíes, siempre verifica." No importa si la petición viene de la red
interna de la oficina o del otro lado del mundo: ambas se autentican y autorizan
con el mismo rigor. No hay "zona de confianza" implícita. Cada solicitud prueba
quién es y qué puede hacer.

## Security by Design (Seguridad desde el Diseño)

La seguridad no se añade al final como un parche. Se diseña desde el primer
diagrama, antes de la primera línea de código: se decide cómo se autentica, cómo
se guardan los secretos, qué datos son sensibles y cómo se protegen, qué puede
salir mal (threat modeling). Reaccionar es caro; diseñar seguro es barato.

> En un repo existente no siempre puedes aplicar Security by Design desde cero,
> pero sí puedes aplicar los demás principios al auditar y al introducir cada
> cambio nuevo.
