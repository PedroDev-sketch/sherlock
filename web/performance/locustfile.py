from locust import HttpUser, task, between, LoadTestShape

class SherlockOSINTUser(HttpUser):
    """
    Simula um usuário real acessando o Sherlock Web.
    """
    wait_time = between(2, 5)

    def on_start(self):
        response = self.client.get("/")
        self.csrftoken = response.cookies.get('csrftoken', '')

    @task(3)
    def visitar_home(self):
        """
        Simula tráfego de navegação simples.
        Representa usuários que abrem o site mas não pesquisam.
        É uma operação rápida e não deve bloquear o servidor.
        """
        self.client.get("/", name="1. Acessar Home")

    @task(1)
    def realizar_busca(self):
        """
        Teste de estresse. 
        Envia o formulário e aciona o gargalo I/O Bound do SherlockService.
        """
        if not self.csrftoken:
            self.on_start()
            
        payload = {
            "username": "alvo_investigacao_locust",
            "csrfmiddlewaretoken": self.csrftoken
        }
        
        with self.client.post("/results/", data=payload, catch_response=True, name="2. Executar Busca OSINT") as response:
            
            if response.status_code == 200:
                if "Timeout ao consultar o serviço upstream" in response.text:
                    response.failure("Timeout do Serviço (Tratado pela View)")
                else:
                    response.success()
            
            elif response.status_code >= 500:
                response.failure(f"Colapso do Servidor (Erro HTTP {response.status_code})")

class PicoDeViralizacao(LoadTestShape):
    """
    Spike Testing (Teste de Pico): Complementa o Load Test tradicional.
    Molda a injeção de usuários simulando um evento de viralização repentina.
    """
    
    stages = [
        {"time": 20, "users": 10, "spawn_rate": 2}, 
        {"time": 40, "users": 200, "spawn_rate": 50}, 
        {"time": 70, "users": 200, "spawn_rate": 10},
        {"time": 100, "users": 15, "spawn_rate": 20},  
        {"time": 120, "users": 5, "spawn_rate": 2},     
    ]

    def tick(self):
        """
        Função chamada pelo Locust a cada segundo para saber quantos
        usuários devem estar ativos neste exato momento.
        """
        run_time = self.get_run_time()

        for stage in self.stages:
            if run_time < stage["time"]:
                tick_data = (stage["users"], stage["spawn_rate"])
                return tick_data

        return None