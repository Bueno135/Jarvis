import os
from typing import List
from core.interfaces import PluginBase, CommandContext, CommandResult

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
        # Extrair caminho (lógica ingênua de string para MVP)
        # Ex: "criar arquivo dados.txt"
        parts = ctx.raw_text.split(" ", 2)
        if len(parts) < 3:
            return CommandResult(False, "Caminho do arquivo não especificado.")
            
        filepath = parts[-1].strip()
        
        # VERIFICAÇÃO DE SEGURANÇA
        security = ctx.kernel.get_service("security")
        if security:
            # Solicitar confirmação para criação de arquivo
            if not security.require_confirmation(f"Criar arquivo: {filepath}"):
                return CommandResult(False, "Ação cancelada pelo usuário.")

        try:
            if os.path.exists(filepath):
                return CommandResult(False, f"O arquivo '{filepath}' já existe.")
                
            with open(filepath, 'w', encoding='utf-8') as f:
                pass # Apenas cria o arquivo vazio
                
            return CommandResult(True, f"Arquivo criado com sucesso: {filepath}")
        except Exception as e:
            return CommandResult(False, f"Erro ao criar arquivo: {str(e)}")

    def _write_to_file(self, ctx: CommandContext) -> CommandResult:
        # Ex: "escrever em notas.txt: Olá Mundo"
        if ":" not in ctx.raw_text:
            return CommandResult(False, "Formato inválido. Use: 'escrever em <arquivo>: <texto>'")
            
        # Separar caminho e conteúdo
        pre_content, content = ctx.raw_text.split(":", 1)
        
        # Tentar extrair o nome do arquivo da primeira parte
        # Isso é frágil e deve ser melhorado com NLP/Regex depois
        parts = pre_content.split(" ")
        filepath = parts[-1].strip()
        content = content.strip()
        
        if not filepath or not content:
            return CommandResult(False, "Arquivo ou conteúdo faltando.")

        # VERIFICAÇÃO DE SEGURANÇA
        security = ctx.kernel.get_service("security")
        if security:
             if not security.require_confirmation(f"Escrever em '{filepath}'"):
                return CommandResult(False, "Ação cancelada pelo usuário.")

        try:
            # Modo 'a' (append) para não sobrescrever acidentalmente tudo, 
            # ou 'w' se for comportamento desejado. Vamos de 'a' por segurança.
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(content + "\n")
                
            return CommandResult(True, f"Texto adicionado a '{filepath}'.")
        except Exception as e:
            return CommandResult(False, f"Erro ao escrever no arquivo: {str(e)}")
