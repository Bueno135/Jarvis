import os
from pathlib import Path
from typing import List
from core.interfaces import PluginBase, CommandContext, CommandResult

# Diretório sandbox — operações de arquivo ficam restritas a esta pasta.
# Usa ~/Jarvis/documents por padrão, mas pode ser configurado.
_SAFE_DIR = os.path.expanduser("~/Jarvis/documents")


def _resolve_safe_path(filepath: str) -> tuple[str, str | None]:
    """
    Resolve o caminho absoluto e verifica se está dentro do sandbox.
    Retorna (caminho_absoluto, None) em caso de sucesso,
    ou (None, mensagem_de_erro) se houver path traversal.
    """
    # Garante que o diretório sandbox existe
    os.makedirs(_SAFE_DIR, exist_ok=True)

    safe_root = os.path.realpath(_SAFE_DIR)
    resolved = os.path.realpath(os.path.join(safe_root, filepath))

    if not resolved.startswith(safe_root + os.sep) and resolved != safe_root:
        return None, (
            f"Acesso negado: o caminho '{filepath}' está fora do diretório permitido "
            f"({_SAFE_DIR}). Path traversal bloqueado."
        )
    return resolved, None


class FileOpsPlugin(PluginBase):
    def name(self) -> str:
        return "FileOps"

    def patterns(self) -> List[str]:
        return [
            "criar arquivo", "create file",
            "escrever em", "write to"
        ]

    def execute(self, ctx: CommandContext) -> CommandResult:
        # Padrões esperados (simplificado):
        # "criar arquivo <caminho>"
        # "escrever em <caminho>: <texto>"
        
        text = ctx.raw_text
        command = ""
        
        # Identificar qual comando foi acionado
        if "criar arquivo" in text or "create file" in text:
            return self._create_file(ctx)
        elif "escrever em" in text or "write to" in text:
            return self._write_to_file(ctx)
            
        return CommandResult(False, "Comando de arquivo não reconhecido.")

    def _create_file(self, ctx: CommandContext) -> CommandResult:
        # Extrair caminho: "criar arquivo dados.txt"
        parts = ctx.raw_text.split(" ", 2)
        if len(parts) < 3:
            return CommandResult(False, "Caminho do arquivo não especificado.")

        raw_filepath = parts[-1].strip()

        # PROTEÇÃO CONTRA PATH TRAVERSAL
        safe_path, error = _resolve_safe_path(raw_filepath)
        if error:
            return CommandResult(False, error)

        # VERIFICAÇÃO DE SEGURANÇA (confirmação do usuário)
        security = ctx.kernel.get_service("security")
        if security:
            if not security.require_confirmation(f"Criar arquivo: {safe_path}"):
                return CommandResult(False, "Ação cancelada pelo usuário.")

        try:
            if os.path.exists(safe_path):
                return CommandResult(False, f"O arquivo já existe: {safe_path}")

            with open(safe_path, 'w', encoding='utf-8') as f:
                pass  # Cria arquivo vazio

            return CommandResult(True, f"Arquivo criado com sucesso: {safe_path}")
        except Exception as e:
            return CommandResult(False, f"Erro ao criar arquivo: {str(e)}")

    def _write_to_file(self, ctx: CommandContext) -> CommandResult:
        # Ex: "escrever em notas.txt: Olá Mundo"
        if ":" not in ctx.raw_text:
            return CommandResult(False, "Formato inválido. Use: 'escrever em <arquivo>: <texto>'")

        # Separar caminho e conteúdo
        pre_content, content = ctx.raw_text.split(":", 1)
        parts = pre_content.split(" ")
        raw_filepath = parts[-1].strip()
        content = content.strip()

        if not raw_filepath or not content:
            return CommandResult(False, "Arquivo ou conteúdo faltando.")

        # PROTEÇÃO CONTRA PATH TRAVERSAL
        safe_path, error = _resolve_safe_path(raw_filepath)
        if error:
            return CommandResult(False, error)

        # VERIFICAÇÃO DE SEGURANÇA (confirmação do usuário)
        security = ctx.kernel.get_service("security")
        if security:
            if not security.require_confirmation(f"Escrever em '{safe_path}'"):
                return CommandResult(False, "Ação cancelada pelo usuário.")

        try:
            # Modo 'a' (append) para não sobrescrever conteúdo existente
            with open(safe_path, 'a', encoding='utf-8') as f:
                f.write(content + "\n")

            return CommandResult(True, f"Texto adicionado a '{safe_path}'.")
        except Exception as e:
            return CommandResult(False, f"Erro ao escrever no arquivo: {str(e)}")
