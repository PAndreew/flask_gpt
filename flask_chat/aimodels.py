import os
from abc import ABC, abstractmethod
from langchain import OpenAI, LLMChain, PromptTemplate
from langchain.memory import ConversationBufferWindowMemory
from langchain.agents import initialize_agent, AgentType
# from langchain.tools import SteamshipImageGenerationTool
from .utils import SteamshipImageGenerationTool

os.environ["STEAMSHIP_API_KEY"] = "0B5C6720-53DC-408F-B0FD-07EC0E6D212F"

ai_model_colors = {
    'openai': '#00A67E',
    # Add more AI models and their colors here as necessary.
}

# AI Model Interface
class AIModelInterface(ABC):

    @abstractmethod
    def generate_response(self, user_input):
        pass


class LLMChainModel(AIModelInterface):

    template = """Assistant is a large language model trained by OpenAI.

    Assistant is designed to be able to assist with a wide range of tasks, from answering simple questions to providing in-depth explanations and discussions on a wide range of topics. As a language model, Assistant is able to generate human-like text based on the input it receives, allowing it to engage in natural-sounding conversations and provide responses that are coherent and relevant to the topic at hand.

    Assistant is constantly learning and improving, and its capabilities are constantly evolving. It is able to process and understand large amounts of text, and can use this knowledge to provide accurate and informative responses to a wide range of questions. Additionally, Assistant is able to generate its own text based on the input it receives, allowing it to engage in discussions and provide explanations and descriptions on a wide range of topics.

    Overall, Assistant is a powerful tool that can help with a wide range of tasks and provide valuable insights and information on a wide range of topics. Whether you need help with a specific question or just want to have a conversation about a particular topic, Assistant is here to assist.

    {history}
    Human: {human_input}
    Assistant:"""

    prompt_template = PromptTemplate(
        input_variables=["history", "human_input"], 
        template=template
    )

    def __init__(self, llm, verbose=True, memory_k=2):
        self.llm_chain = LLMChain(
            llm=llm, 
            prompt=self.prompt_template, 
            verbose=verbose, 
            memory=ConversationBufferWindowMemory(k=memory_k),
        )

    def generate_response(self, user_input):
        # Use the LLMChain model to generate a response
        response = self.llm_chain.predict(human_input=user_input)
        return response

# Specific subclasses for each LLM
class OpenAILLMChain(LLMChainModel):
    def __init__(self, temperature=0, verbose=True, memory_k=2):
        super().__init__(llm=OpenAI(temperature=temperature), verbose=verbose, memory_k=memory_k)


# Class for Generative AI models
class GenerativeAIModel(AIModelInterface):

    def __init__(self, temperature=0, verbose=True, model_name="dall-e", agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION):
        self.llm = OpenAI(temperature=temperature)
        tools = [SteamshipImageGenerationTool(model_name=model_name)]
        self.agent = initialize_agent(tools, self.llm, agent=agent_type, verbose=verbose)

    def generate_response(self, user_input):
        # Use the Generative AI model to generate a response
        response = self.agent.run(user_input)
        return response


# AI Model Manager
class AIModelManager:

    def __init__(self, model_name='openai'):
        self.models = {
            'openai': OpenAILLMChain(),
            # 'generative': GenerativeAIModel(),
            # Add more models as needed
        }
        if model_name in self.models:
            self.current_model = self.models[model_name]
        else:
            # Handle invalid model_name
            pass
        self.current_model_name = model_name
        self.last_response = None

    def generate_response(self, user_input):
        while True:
            response = self.current_model.generate_response(user_input)
            if response != self.last_response:
                self.last_response = response
                return response
