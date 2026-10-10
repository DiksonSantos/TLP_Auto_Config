const Applet = imports.ui.applet;
const PopupMenu = imports.ui.popupMenu;
const Main = imports.ui.main;
const Util = imports.misc.util;
const GLib = imports.gi.GLib;
const Gio = imports.gi.Gio;
const ByteArray = imports.byteArray;
const Mainloop = imports.mainloop;
const AppletManager = imports.ui.appletManager;

// =================== Configurações ===================
const HOME = GLib.get_home_dir();
const SCRIPT_PATH  = HOME + "/Linux_Helper/TLP_Power_Management/SUDO_CPU_2key.py";
const ICON_PERFIL  = HOME + "/Features/Icones/Perfil_Energia.png";
// Ajuste para o local onde está o seu programa completo de monitoramento:
const MONITOR_SCRIPT = HOME + "/Linux_Helper/TLP_Power_Management/PowerManagement_And_Monitoring.py";

// [nome do módulo Python, texto exibido]
const PERFIS = [
    ["Turbo",    "🚀 Turbo"],
    ["Padrao",   "⚙️ Padrão"],
    ["Economia", "🔋 Economia"],
    ["Auto",     "🤖 Auto"]
];

const RE_PERFIL_LEITURA = /from\s+(\w+)\s+import\s+determine_governor/;
const RE_PERFIL_TROCA   = /from\s+\w+\s+import\s+determine_governor,\s*apply_pcie_policy/;

class PowerProfileApplet extends Applet.IconApplet {
    constructor(metadata, orientation, panel_height, instance_id) {
        super(orientation, panel_height, instance_id);
        this._uuid = metadata.uuid;
        this._instanceId = instance_id;

        if (GLib.file_test(ICON_PERFIL, GLib.FileTest.EXISTS))
            this.set_applet_icon_path(ICON_PERFIL);
        else
            this.set_applet_icon_name("battery");

        this.menuManager = new PopupMenu.PopupMenuManager(this);
        this.menu = new Applet.AppletPopupMenu(this, orientation);
        this.menuManager.addMenu(this.menu);

        this.itens = {};
        for (let [modulo, rotulo] of PERFIS) {
            let item = new PopupMenu.PopupMenuItem(rotulo);
            item.connect("activate", () => this._aplicarPerfil(modulo, rotulo));
            this.menu.addMenuItem(item);
            this.itens[modulo] = item;
        }

        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());
        let abrir = new PopupMenu.PopupMenuItem("📊 Abrir monitor completo");
        abrir.connect("activate", () => {
            Util.spawnCommandLine('python3 "' + MONITOR_SCRIPT + '"');
        });
        this.menu.addMenuItem(abrir);

        let sair = new PopupMenu.PopupMenuItem("❌ Sair (remover da barra)");
        sair.connect("activate", () => this._sair());
        this.menu.addMenuItem(sair);

        this.menu.connect("open-state-changed", (menu, aberto) => {
            if (aberto) this._atualizar();
        });

        this._atualizar();
        this._timer = Mainloop.timeout_add_seconds(10, () => {
            this._atualizar();
            return true;
        });
    }

    on_applet_clicked() {
        this.menu.toggle();
    }

    on_applet_removed_from_panel() {
        if (this._timer) {
            Mainloop.source_remove(this._timer);
            this._timer = null;
        }
    }

    _sair() {
        try {
            AppletManager._removeAppletFromPanel(this._uuid, this._instanceId);
        } catch (e) {
            Main.notifyError("Perfil de Energia",
                "Não foi possível remover: " + e.message +
                "\nUse botão direito no ícone > Remover.");
        }
    }

    _lerScript() {
        let [ok, bytes] = GLib.file_get_contents(SCRIPT_PATH);
        if (!ok) throw new Error("Não foi possível ler " + SCRIPT_PATH);
        return ByteArray.toString(bytes);
    }

    _perfilAtual() {
        try {
            let m = this._lerScript().match(RE_PERFIL_LEITURA);
            return m ? m[1] : null;
        } catch (e) {
            return null;
        }
    }

    _marcar(item, selecionado) {
        if (typeof item.setOrnament === "function" && PopupMenu.OrnamentType)
            item.setOrnament(PopupMenu.OrnamentType.DOT, selecionado);
        else if (typeof item.setShowDot === "function")
            item.setShowDot(selecionado);
    }

    _atualizar() {
        let atual = this._perfilAtual();
        for (let modulo in this.itens)
            this._marcar(this.itens[modulo], modulo === atual);
        this.set_applet_tooltip("Perfil de energia: " + (atual || "Desconhecido"));
    }

    _aplicarPerfil(modulo, rotulo) {
        try {
            let conteudo = this._lerScript();
            if (!RE_PERFIL_TROCA.test(conteudo))
                throw new Error("Linha de import do perfil não encontrada no script.");

            let novo = conteudo.replace(
                RE_PERFIL_TROCA,
                "from " + modulo + " import determine_governor, apply_pcie_policy"
            );

            let arquivo = Gio.File.new_for_path(SCRIPT_PATH);
            arquivo.replace_contents(
                ByteArray.fromString(novo), null, false,
                Gio.FileCreateFlags.NONE, null
            );

            this._atualizar();
            Main.notify("Perfil de energia", "Perfil aplicado: " + rotulo);
        } catch (e) {
            Main.notifyError("Perfil de energia", "Erro ao aplicar perfil: " + e.message);
        }
    }
}

function main(metadata, orientation, panel_height, instance_id) {
    return new PowerProfileApplet(metadata, orientation, panel_height, instance_id);
}
