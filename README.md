# MikroBot Pro X — pronto para compilar

## No Codespaces

Entre na pasta do pacote e rode:

```bash
chmod +x build_apk.sh prepare_download.sh
./build_apk.sh
```

O script configura automaticamente o caminho do Android SDK e usa o Gradle existente. Se não houver Gradle, baixa a versão necessária.

Depois:

```bash
./prepare_download.sh
```

Será criado:

```text
MikroBot-Pro-X-debug.apk
```

Esse é o arquivo que você baixa para o Android e instala.

## Python Core

Para rodar o servidor:

```bash
chmod +x start_mikrobot.sh
PORT=8765 ./start_mikrobot.sh
```

Outra porta:

```bash
PORT=8080 ./start_mikrobot.sh
```

O APK contém a interface HTML local. O Python Core é um serviço separado no Codespace; ele não é executado dentro do APK automaticamente.

## Importante

O APK é uma compilação de debug. Para distribuir publicamente, é recomendável criar uma assinatura de release.
