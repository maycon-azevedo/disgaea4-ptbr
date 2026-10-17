# Disgaea 4 Complete+ — Tradução PT-BR

![Disgaea 4 Complete+](imagens/capa.jpg)

Tradução de fã para **português do Brasil** da versão Steam de *Disgaea 4 Complete+*.
Tradução por **Maykin**.

<p>
  <img src="imagens/print1.jpg" width="49%" alt="Menu traduzido">
  <img src="imagens/print2.jpg" width="49%" alt="Diálogo traduzido">
</p>

## ⬇️ Download

Baixe o `.zip` mais recente na página de **[Releases](https://github.com/maycon-azevedo/disgaea4-ptbr/releases/latest)**.

## O que está traduzido

- Toda a história, cenas e diálogos (inclusive pós-jogo, DLCs, Fuka & Desco Show e Salto no Tempo)
- Interface, menus e tutoriais
- Descrições de itens, skills, evilities, innocents e classes
- Bestiário, projetos do Senado, Geo Effects, sala de tortura, falas dos NPCs da base e mais

Nomes próprios, nomes de itens/skills/classes e termos do jogo (Netherworld, Prinny, Item World, Evility...)
foram mantidos em inglês de propósito. Algumas falas que só existem em japonês no jogo original continuam em japonês.

## Como instalar

1. Feche o jogo.
2. Extraia o `.zip` e execute **`Instalar_Traducao_PTBR_Disgaea4.exe`**.
3. O instalador encontra o jogo na Steam sozinho. Se não achar, clique em **Procurar...** e selecione a pasta
   `Disgaea 4 Complete+` (Steam → botão direito no jogo → Gerenciar → Ver arquivos locais).
4. Clique em **Instalar tradução**.
5. Jogue com o idioma em **inglês**. A tradução substitui o texto em inglês.

Para **desinstalar**, abra o instalador e clique em **Desinstalar (voltar ao inglês)**. Outra opção é usar
*Verificar integridade dos arquivos* na Steam.

### "O Windows protegeu o computador"

O instalador não tem assinatura digital paga, então o Windows SmartScreen pode mostrar esse aviso.
Clique em **Mais informações** → **Executar assim mesmo**.

### Steam Deck / Linux

O instalador é para Windows. No Steam Deck ou no Linux ele pode funcionar pelo Proton/Wine,
mas isso não foi testado.

## Segurança

O instalador:
- só altera `Data\DATA\EN\DATABASE_EN.dat` e `Data\DATA\EN\EN_GameString.dat`;
- antes de alterar, confere se os arquivos são exatamente os da versão suportada (SHA256);
- guarda os originais em `Data\DATA\EN\backup_original_ptbr\`.

Alguns antivírus acusam falso positivo em programas Python empacotados com PyInstaller.
O código-fonte completo do instalador está na pasta [`src/`](src/), e o hash SHA256 de cada versão
está na página da release.

## Onde está o texto da tradução?

O texto traduzido **não fica neste repositório**. Ele vai embutido no instalador (arquivo `traducao_ptbr.bin`,
só com o texto em português, compactado), e o instalador aplica esse texto nos arquivos do seu jogo.

Os arquivos de trabalho da tradução não são publicados porque contêm o roteiro original em inglês, que pertence
à NIS America. Este repositório tem só o código do instalador, para quem quiser conferir o que ele faz.

## Encontrou um erro?

Abra uma **[Issue](https://github.com/maycon-azevedo/disgaea4-ptbr/issues)** com:
- a frase (em inglês ou português);
- onde ela aparece (capítulo, NPC, menu);
- um print, se puder.

## Aviso legal

Projeto de fã, sem fins lucrativos e sem vínculo com a Nippon Ichi Software ou a NIS America.
É preciso ter o jogo original. Este repositório e os downloads **não contêm arquivos do jogo**, só o texto
traduzido e o programa que o aplica. *Disgaea* e as imagens relacionadas pertencem aos seus donos.
