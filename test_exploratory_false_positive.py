import subprocess
import sys

def main():
    print("=" * 60)
    print("INICIANDO TESTE EXPLORATÓRIO: Falso Positivo (BoardGameGeek)")
    print("Técnica: Adivinhação de Erros / Limite de Caracteres")
    print("=" * 60)
    
    # Hash gigante e aleatório (muito maior que 20 caracteres)
    fake_username = "hjsdh238947jhsdjh238947_teste_exploratorio_extremo"
    
    print(f"\n[INFO] Usuário de teste: '{fake_username}'")
    print("[INFO] Alvo: Apenas o site 'BoardGameGeek'")
    print("[INFO] Aguardando resposta do Sherlock...\n")
    
    # Chamando o sherlock como subprocesso focado no site vulnerável
    cmd = [
        sys.executable, "-m", "sherlock_project", 
        fake_username, 
        "--site", "BoardGameGeek", 
        "--print-found"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Imprimir o output original do Sherlock
    print(result.stdout)
    
    # Validando o resultado
    if "BoardGameGeek" in result.stdout:
        print("=" * 60)
        print(">>> SUCESSO NO TESTE EXPLORATÓRIO! <<<")
        print("O Sherlock reportou que o usuário existe (FALSO POSITIVO).")
        print("Motivo: A API do BoardGameGeek limitou o tamanho da string")
        print("e retornou validação falsa, quebrando a heurística do Sherlock.")
        print("=" * 60)
    else:
        print("O Sherlock não detectou o Falso Positivo (comportamento inesperado).")

if __name__ == "__main__":
    main()
