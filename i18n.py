# -*- coding: utf-8 -*-
"""JatLog — 画面に出る文言（ポルトガル語・英語・日本語）。

ポルトガル語が原文で、既定でもある（現場が使うのはこれ）。他の言語は
データを見返す人のためのもの。

言語を足すときは、同じキーを持つ塊を TEXTS に1つ増やして LANGS に1行足すだけ。
app.py 側は何も変えなくてよい。
⚠ 文言を足したら3言語すべてに足すこと（欠けたキーはポルトガル語に落ちる）。

⚠ ここにあるのは「画面に出る文字」だけ。スプレッドシートに書き込む値
（月名 Aug-26、単位 kg/g、監査ログの CREATE/EDIT/DELETE など）は言語に関係なく
従来どおり英語のまま。

文中の {x} は該当する値に置き換わる。
"""

# (コード, ボタンに出す表記)
LANGS = [
    ("pt", "PT"),
    ("en", "EN"),
    ("ja", "日本語"),
]

TEXTS = {

    "pt": {
        # 画面に表示する小数点。読み取りは常に「.」「,」の両方を受け付ける
        # （app.py の parse_number を参照）。
        "num.separador": ",",

        "activacao.titulo": "Ativar o aparelho",
        "activacao.texto": "Digite o código de activação que o gestor lhe deu. "
                           "Só é preciso uma vez em cada aparelho.",
        "activacao.campo": "Código de activação",
        "activacao.campoPlaceholder": "Código do gestor",
        "activacao.botao": "Ativar",
        "activacao.errado": "Código de activação incorreto.",

        "entrada.titulo": "Registro de colheita",
        "entrada.texto": "Identifique-se para começar. O nome fica guardado até você trocar de usuário.",
        "entrada.nome": "Nome de usuário",
        "entrada.nomePlaceholder": "Seu nome",
        "entrada.adminActivo": "Modo administrador ativo — você continuará como administrador.",
        "entrada.sairAdmin": "Sair do modo administrador",
        "entrada.admin": "Administrador",
        "entrada.senha": "Senha do administrador",
        "entrada.senhaPlaceholder": "Somente para o gestor",
        "entrada.botao": "Começar",
        "entrada.senhaErrada": "Senha do administrador incorreta.",
        "entrada.faltaNome": "Informe seu nome.",

        "local.titulo": "Escolha o local e o mês",
        "local.usuario": "Usuário: <b>{nome}</b>",
        "local.usuarioAdmin": "Usuário: <b>{nome}</b> · administrador",
        "local.local": "Local",
        "local.mes": "Mês",
        "local.ano": "Ano",
        "local.botao": "Continuar",

        "geral.trocarUsuario": "Trocar de usuário",
        "geral.cancelar": "Cancelar",

        "dados.erro": "Não foi possível carregar os dados. {erro}",
        "dados.tentar": "Tentar novamente",

        "topo.registros": "registros",

        "busca.mesAdmin": "Mês (administrador)",
        "busca.ajuda": "Digite o número e toque em Enter para avançar.",
        "busca.mudarLocal": "Mudar local ou mês",
        "busca.soNumeros": "Digite apenas números.",
        "busca.gravado": "<b>{linha}</b> — {valor} {unidade} salvo às {hora}",

        "candidatos.aviso": "O número <b>{numero}</b> aparece em {n} registros. "
                            "Escolha em qual deles você vai lançar o peso.",
        "candidatos.jaRegistado": "JÁ REGISTRADO",
        "candidatos.outro": "Buscar outro número",

        "peso.tag": "Pesando",
        "peso.campo": "Peso",
        "peso.registar": "Registrar",
        "peso.aRegistar": "Registrando…",
        "peso.invalido": "Valor inválido. Use apenas números — tanto faz 1,5 como 1.5",
        "peso.maiorQueZero": "O peso deve ser maior que zero.",
        "peso.faltaPeso": "Informe o novo peso.",
        "peso.mae": "ID da mãe",
        "peso.variedade": "Variedade",
        "peso.saco": "Saco",
        "peso.plantas": "Plantas",
        "peso.plantasMin": "plantas",

        "confirmar.tag": "Confirmar registro",
        "confirmar.aviso": "O valor <b>{valor} {unidade}</b> está fora da faixa esperada. "
                           "Confirme se está correto antes de registrar.",
        "confirmar.assim": "Registrar assim",
        "confirmar.corrigir": "Corrigir",

        "editar.tag": "Editando registro",
        "editar.cabecalho": "Corrigindo o peso registrado para <b>{linha}</b>. Ajuste o valor e salve.",
        "editar.lancado": "Lançado em {quando} por {quem}",
        "editar.campo": "Novo peso",
        "editar.guardar": "Salvar",
        "editar.aGuardar": "Salvando…",
        "editar.apagar": "Excluir este registro",
        "editar.semPermissao": "Somente o autor do registro ou o administrador pode alterá-lo.",

        "apagar.tag": "Registro a excluir",
        "apagar.aviso": "Excluir definitivamente o registro de <b>{linha}</b> "
                        "({valor} {unidade})? Esta ação não pode ser desfeita.",
        "apagar.sim": "Sim, excluir",
        "apagar.nao": "Não, voltar",
        "apagar.aApagar": "Excluindo…",

        "historico.titulo": "Últimos registros",
        "historico.vazio": "Nenhum registro em {mes} ainda.",
        "historico.toque": "toque para corrigir",
        "historico.voce": "você",
        "historico.trancado": "🔒 só o autor ou o admin",

        "rede.semRede": "SEM CONEXÃO — aguarde o sinal voltar antes de registrar",
        "erro.gravar": "Falha de conexão — o registro NÃO foi salvo. "
                       "Verifique o sinal e toque em Registrar novamente.",
        "erro.desactualizado": "Este registro mudou ou foi excluído em outro aparelho. "
                               "A lista foi atualizada — confira antes de tentar de novo.",

        "brinde.registado": "{linha} registrado",
        "brinde.actualizado": "{linha} atualizado",
        "brinde.apagado": "{linha} excluído",

        "sitio.lines.busca": "Número inicial da linha",
        "sitio.lines.buscaCampo": "Número da linha",
        "sitio.lines.naoExiste": "Linha {v} não existe no cadastro.",
        "sitio.lines.jaRegistado": "Esta linha já tem um registro neste mês. "
                                   "Um novo lançamento será somado ao histórico.",
        "sitio.lines.plural": "linhas",
        "sitio.lines.unico": "Linha única",
        "sitio.blocks.busca": "Número inicial do bloco",
        "sitio.blocks.buscaCampo": "Número do bloco",
        "sitio.blocks.naoExiste": "Bloco {v} não existe no cadastro.",
        "sitio.blocks.jaRegistado": "Este bloco já tem um registro neste mês. "
                                    "Um novo lançamento será somado ao histórico.",
        "sitio.blocks.plural": "blocos",
        "sitio.blocks.unico": "Bloco único",
    },

    "en": {
        "num.separador": ".",

        "activacao.titulo": "Activate this phone",
        "activacao.texto": "Enter the activation code your manager gave you. "
                           "You only need to do this once on each phone.",
        "activacao.campo": "Activation code",
        "activacao.campoPlaceholder": "Manager's code",
        "activacao.botao": "Activate",
        "activacao.errado": "Wrong activation code.",

        "entrada.titulo": "Harvest log",
        "entrada.texto": "Enter your name to start. It stays until you switch user.",
        "entrada.nome": "User name",
        "entrada.nomePlaceholder": "Your name",
        "entrada.adminActivo": "Administrator mode is on — you will stay an administrator.",
        "entrada.sairAdmin": "Leave administrator mode",
        "entrada.admin": "Administrator",
        "entrada.senha": "Administrator password",
        "entrada.senhaPlaceholder": "Manager only",
        "entrada.botao": "Start",
        "entrada.senhaErrada": "Wrong administrator password.",
        "entrada.faltaNome": "Enter your name.",

        "local.titulo": "Choose the site and the month",
        "local.usuario": "User: <b>{nome}</b>",
        "local.usuarioAdmin": "User: <b>{nome}</b> · administrator",
        "local.local": "Site",
        "local.mes": "Month",
        "local.ano": "Year",
        "local.botao": "Continue",

        "geral.trocarUsuario": "Switch user",
        "geral.cancelar": "Cancel",

        "dados.erro": "The data could not be loaded. {erro}",
        "dados.tentar": "Try again",

        "topo.registros": "records",

        "busca.mesAdmin": "Month (administrator)",
        "busca.ajuda": "Type the number and press Enter to continue.",
        "busca.mudarLocal": "Change site or month",
        "busca.soNumeros": "Numbers only.",
        "busca.gravado": "<b>{linha}</b> — {valor} {unidade} saved at {hora}",

        "candidatos.aviso": "Number <b>{numero}</b> appears in {n} entries. "
                            "Choose the one you are weighing.",
        "candidatos.jaRegistado": "ALREADY RECORDED",
        "candidatos.outro": "Search another number",

        "peso.tag": "Weighing",
        "peso.campo": "Weight",
        "peso.registar": "Record",
        "peso.aRegistar": "Recording…",
        "peso.invalido": "Invalid value. Numbers only — either 1.5 or 1,5 works",
        "peso.maiorQueZero": "The weight must be greater than zero.",
        "peso.faltaPeso": "Enter the new weight.",
        "peso.mae": "Mother ID",
        "peso.variedade": "Variety",
        "peso.saco": "Sack",
        "peso.plantas": "Plants",
        "peso.plantasMin": "plants",

        "confirmar.tag": "Confirm the entry",
        "confirmar.aviso": "<b>{valor} {unidade}</b> is outside the expected range. "
                           "Check it before recording.",
        "confirmar.assim": "Record it anyway",
        "confirmar.corrigir": "Fix it",

        "editar.tag": "Editing an entry",
        "editar.cabecalho": "Correcting the weight recorded for <b>{linha}</b>. "
                            "Adjust the value and save.",
        "editar.lancado": "Recorded on {quando} by {quem}",
        "editar.campo": "New weight",
        "editar.guardar": "Save",
        "editar.aGuardar": "Saving…",
        "editar.apagar": "Delete this entry",
        "editar.semPermissao": "Only the person who recorded it, or an administrator, can change it.",

        "apagar.tag": "Entry to delete",
        "apagar.aviso": "Permanently delete the entry for <b>{linha}</b> "
                        "({valor} {unidade})? This cannot be undone.",
        "apagar.sim": "Yes, delete",
        "apagar.nao": "No, go back",
        "apagar.aApagar": "Deleting…",

        "historico.titulo": "Latest entries",
        "historico.vazio": "No entries in {mes} yet.",
        "historico.toque": "tap to correct",
        "historico.voce": "you",
        "historico.trancado": "🔒 only the author or an admin",

        "rede.semRede": "NO CONNECTION — wait for the signal before recording",
        "erro.gravar": "Connection failed — the entry was NOT saved. "
                       "Check the signal and tap Record again.",
        "erro.desactualizado": "This entry was changed or deleted on another phone. "
                               "The list has been refreshed — check it before trying again.",

        "brinde.registado": "{linha} recorded",
        "brinde.actualizado": "{linha} updated",
        "brinde.apagado": "{linha} deleted",

        "sitio.lines.busca": "First line number",
        "sitio.lines.buscaCampo": "Line number",
        "sitio.lines.naoExiste": "Line {v} is not in the register.",
        "sitio.lines.jaRegistado": "This line already has an entry this month. "
                                   "A new one will be added to the history.",
        "sitio.lines.plural": "lines",
        "sitio.lines.unico": "Single line",
        "sitio.blocks.busca": "First block number",
        "sitio.blocks.buscaCampo": "Block number",
        "sitio.blocks.naoExiste": "Block {v} is not in the register.",
        "sitio.blocks.jaRegistado": "This block already has an entry this month. "
                                    "A new one will be added to the history.",
        "sitio.blocks.plural": "blocks",
        "sitio.blocks.unico": "Single block",
    },

    "ja": {
        "num.separador": ".",

        "activacao.titulo": "この端末を有効にする",
        "activacao.texto": "管理者から渡されたアクティベーションコードを入力してください。"
                           "端末ごとに最初の一度だけです。",
        "activacao.campo": "アクティベーションコード",
        "activacao.campoPlaceholder": "管理者から渡されたコード",
        "activacao.botao": "有効にする",
        "activacao.errado": "アクティベーションコードが違います。",

        "entrada.titulo": "収穫記録",
        "entrada.texto": "名前を入れて始めてください。ユーザーを切り替えるまで保持されます。",
        "entrada.nome": "ユーザー名",
        "entrada.nomePlaceholder": "あなたの名前",
        "entrada.adminActivo": "管理者モードが有効です。このまま管理者として続けます。",
        "entrada.sairAdmin": "管理者モードを終了する",
        "entrada.admin": "管理者",
        "entrada.senha": "管理者パスワード",
        "entrada.senhaPlaceholder": "管理者のみ",
        "entrada.botao": "開始",
        "entrada.senhaErrada": "管理者パスワードが違います。",
        "entrada.faltaNome": "名前を入力してください。",

        "local.titulo": "拠点と月を選ぶ",
        "local.usuario": "ユーザー: <b>{nome}</b>",
        "local.usuarioAdmin": "ユーザー: <b>{nome}</b> · 管理者",
        "local.local": "拠点",
        "local.mes": "月",
        "local.ano": "年",
        "local.botao": "次へ",

        "geral.trocarUsuario": "ユーザーを切り替える",
        "geral.cancelar": "やめる",

        "dados.erro": "データを読み込めませんでした。{erro}",
        "dados.tentar": "もう一度試す",

        "topo.registros": "件",

        "busca.mesAdmin": "月（管理者）",
        "busca.ajuda": "番号を入力して Enter を押してください。",
        "busca.mudarLocal": "拠点・月を変える",
        "busca.soNumeros": "数字だけを入力してください。",
        "busca.gravado": "<b>{linha}</b> — {valor} {unidade} を {hora} に保存しました",

        "candidatos.aviso": "番号 <b>{numero}</b> は {n} 件あります。計量する対象を選んでください。",
        "candidatos.jaRegistado": "登録済み",
        "candidatos.outro": "別の番号を探す",

        "peso.tag": "計量中",
        "peso.campo": "重量",
        "peso.registar": "登録",
        "peso.aRegistar": "登録しています…",
        "peso.invalido": "入力が正しくありません。数字だけを入れてください（1.5 でも 1,5 でも構いません）",
        "peso.maiorQueZero": "重量は0より大きい値にしてください。",
        "peso.faltaPeso": "新しい重量を入力してください。",
        "peso.mae": "母樹ID",
        "peso.variedade": "品種",
        "peso.saco": "袋",
        "peso.plantas": "株数",
        "peso.plantasMin": "株",

        "confirmar.tag": "登録の確認",
        "confirmar.aviso": "<b>{valor} {unidade}</b> は想定の範囲外です。"
                           "正しいか確認してから登録してください。",
        "confirmar.assim": "このまま登録",
        "confirmar.corrigir": "入力し直す",

        "editar.tag": "記録の修正",
        "editar.cabecalho": "<b>{linha}</b> の重量を修正します。値を直して保存してください。",
        "editar.lancado": "{quando} に {quem} が登録",
        "editar.campo": "新しい重量",
        "editar.guardar": "保存",
        "editar.aGuardar": "保存しています…",
        "editar.apagar": "この記録を削除する",
        "editar.semPermissao": "登録した本人か管理者だけが変更できます。",

        "apagar.tag": "削除する記録",
        "apagar.aviso": "<b>{linha}</b> の記録（{valor} {unidade}）を完全に削除しますか。"
                        "元に戻せません。",
        "apagar.sim": "はい、削除する",
        "apagar.nao": "いいえ、戻る",
        "apagar.aApagar": "削除しています…",

        "historico.titulo": "最近の記録",
        "historico.vazio": "{mes} の記録はまだありません。",
        "historico.toque": "タップして修正",
        "historico.voce": "あなた",
        "historico.trancado": "🔒 本人と管理者のみ",

        "rede.semRede": "圏外 — 電波が戻ってから登録してください",
        "erro.gravar": "通信に失敗しました。記録は保存されていません。"
                       "電波を確認してもう一度「登録」を押してください。",
        "erro.desactualizado": "この記録は別の端末で変更または削除されました。"
                               "一覧を更新したので、確認してからやり直してください。",

        "brinde.registado": "{linha} を登録しました",
        "brinde.actualizado": "{linha} を更新しました",
        "brinde.apagado": "{linha} を削除しました",

        "sitio.lines.busca": "ラインの開始番号",
        "sitio.lines.buscaCampo": "ライン番号",
        "sitio.lines.naoExiste": "ライン {v} は台帳にありません。",
        "sitio.lines.jaRegistado": "このラインは今月すでに記録があります。"
                                   "新しい記録は履歴に追加されます。",
        "sitio.lines.plural": "ライン",
        "sitio.lines.unico": "単一ライン",
        "sitio.blocks.busca": "ブロックの開始番号",
        "sitio.blocks.buscaCampo": "ブロック番号",
        "sitio.blocks.naoExiste": "ブロック {v} は台帳にありません。",
        "sitio.blocks.jaRegistado": "このブロックは今月すでに記録があります。"
                                    "新しい記録は履歴に追加されます。",
        "sitio.blocks.plural": "ブロック",
        "sitio.blocks.unico": "単一ブロック",
    },
}

# 日本語のときだけ被せるスタイル。欧文向けの letter-spacing と大文字化は、
# 日本語だと「ユ ー ザ ー 名」のように間延びして読みにくくなる。
CSS_JA = """
<style>
.topbar .who .month, .badge-adm, .counter .lbl, .eyebrow, .readout .tag,
.meta .k, .login-head .mark, .appfoot,
.st-key-loginpanel label, .st-key-adminmonthrow label {
  letter-spacing: 0 !important;
  text-transform: none !important;
}
</style>
"""
