import itertools
import pickle as pkl
import spacy
import scispacy
from spacy_utils import *
from utils import *


class Linked_Entities():
    def __init__(self, resolve_abbreviations: bool, ontology: str, threshold: float, 
                 max_entities_per_mention: int) -> None:
        
        self.resolve_abbreviations = resolve_abbreviations
        self.ontology = ontology
        self. threshold = threshold
        self.max_entities_per_mention = max_entities_per_mention
        self.linker = EntityLinker(resolve_abbreviations=self.resolve_abbreviations, 
                                   name=self.ontology, threshold=self.threshold, 
                                   max_entities_per_mention=self.max_entities_per_mention)


    def connectedEntities(self, entity: str, list_linked_entities) -> list[list[str], list[str]]:
        '''
        Creamos una función para que, dado una entidad "scispacy.linking_utils.Entity" 
        nos devuelva las entidades conectadas en una lista y otra lista con sus respectivos 
        TUIs, esto nos ayudará a filtrar por TUIs si nos interesa.

        Esta función recibe como entrada la entidad de la que se quieren sacar las conexiones 
        en formato string, así como una pipeline de spacy en la que se ha cargado un modelo en 
        inglés y realiza NER sobre entidades del dominio médico. También requiere un linker de
        scispacy que cargará en memoria la ontología empleada para realizar EntityLinking sobre 
        las entidades detectadas en la pipeline, devolviendo los datos completos de estas entidades.
        '''
    
        entity_list = []
        TUI_list = []

        for entities in range(len(list_linked_entities)):
            target_entity = list_linked_entities[entities][0].lower()
            if entity.lower() == target_entity:
                new_linked_entities = list_linked_entities[entities][1]
                for new_linked_entity in new_linked_entities:
                    new_linked_entity = self.linker.kb.cui_to_entity[new_linked_entity[0]]
                    new_linked_entity_name =  new_linked_entity.canonical_name
                    if not new_linked_entity_name.lower() == entity.lower():
                        entity_list.append(new_linked_entity.canonical_name)
                        TUI_list.append(new_linked_entity.types)
        return entity_list, TUI_list


    def connectedEntitiesWithSelf(self, linked_entities) -> list[list[str], list[str]]:
        '''
        entity: el nombre de la entidad que vamos a utilizar para sus conexiones
        nlp: una pipeline de spacy que realice NER en el campo médico sobre un modelo en inglés
        linker: un linker de scispacy que nos permita conectar las entidades con UMLS u otra ontología soportada por scispacy
        '''
    
        entity_list = []
        TUI_list = []
        for entidad in linked_entities:
            for entidades_nuevas in entidad[1]:
                new_entity = self.linker.kb.cui_to_entity[entidades_nuevas[0]]
                entity_list.append(new_entity.canonical_name)
                TUI_list.append(new_entity.types)
     
        return entity_list, TUI_list


    def TUIfilter(entity_list: [list[str]], TUI_list: list[list[str]], goldenTUIs: list[str]) -> list[list[str], list[str]]:
        
        '''
        Función para que filtre las entidades de una lista en base a unos TUIs de referencia
        '''

        new_TUI_list = []
        new_entity_list = []
        for goldenTUI in range(len(goldenTUIs)):
            for TUIs in range(len(TUI_list)):
                for TUI in TUI_list[TUIs]:
                    if goldenTUIs[goldenTUI] == TUI:
                        new_TUI_list.append(TUI)
                        new_entity_list.append(entity_list[TUIs])
        
        return new_entity_list, new_TUI_list


    def getEntitiesAndTUIs(self, list_linked_entities):
        entities = []
        TUIs_list = []
        
        for entity in list_linked_entities:
            TUIs = []
            CUIs = entity[1]
            for CUI in CUIs:
                new_entity = self.linker.kb.cui_to_entity[CUI[0]]
                TUI = new_entity.types
                TUIs.append(TUI)
            TUIs = list(itertools.chain.from_iterable(TUIs))
            TUIs = list(set(TUIs))
            entities.append(entity[0].lower())
            TUIs_list.append(TUIs)
        
        return entities, TUIs_list

    '''
    Esta función verifica cuales son las palabras candidatas para hacer desambiguación 
    en grupos semánticos. La condición para que una palabra sea candidata es que, tras 
    realizar el NER que lleva a cabo la pipeline exista más de 1 TUI para la palabra detectada.
    '''

    def candidatesChecker(self, list_linked_entities):
        """
        Check the candidates from the list of linked entities based on their TUIs.

        Args:
            list_linked_entities (list): List of linked entities, where each entity is a tuple containing CUIs.

        Returns:
            tuple: A tuple containing two lists - candidates and TUIs_list.
                - candidates: List of entities that have more than one TUI.
                - TUIs_list: List of TUIs associated with each candidate entity.
        """
        candidates = []
        TUIs_list = []

        for entity in list_linked_entities:
            TUIs = []
            CUIs = entity[1]
            for CUI in CUIs:
                new_entity = self.linker.kb.cui_to_entity[CUI[0]]
                TUI = new_entity.types
                TUIs.append(TUI)
            TUIs = list(itertools.chain.from_iterable(TUIs))
            TUIs = list(set(TUIs)) 
            if len(TUIs) > 1:
                candidates.append(entity[0])
                TUIs_list.append(TUIs)
        return candidates, TUIs_list

    '''
    Esta función cumple, sin embargo si alguna de las entidades tiene dos TUIs 
    que corresponden con los golden TUIs esa entidad y sus TUIs se copiarán dos veces.
    (cada copia llevará asociado un TUI diferente como se muestra en la siguiente celda)
    '''      

    def otherRelatedEntities(self, candidate,
                            candidate_TUIs, 
                            entity_list, TUI_list):
        
        '''
        Esta función nos indica para una entidad dada del texto cuales son las entidades
        relacionadas con la misma (porque comparten alguno de sus TUIs) encontradas en el 
        mismo texto.
        '''
        related_entities = []
        related_TUIs = []
        for entity in range(len(TUI_list)):
            TUIs = TUI_list[entity]
            for candidate_TUI in candidate_TUIs:
                if candidate_TUI[0] in TUIs:
                    related_entities.append(entity_list[entity])
                    break
            related_entities = list(set(related_entities))

            if candidate in related_entities:
                index = related_entities.index(candidate)
                related_entities.remove(candidate)
  
        for entity in related_entities:
            index = entity_list.index(entity)
            TUIs = TUI_list[index]
            TUIs = list(set(TUIs))
            related_TUIs.append(TUIs)

        return related_entities, related_TUIs


    def column_of_entities(self, entities: list[str], list_linked_entities):
        column_entities = []
        column_TUIs = []
        for entity in entities:
            entities, TUIs = self.connectedEntities(entity, list_linked_entities)
            column_entities.append(entities)
            column_TUIs.append(TUIs)
        return column_entities[0], column_TUIs[0]
    

    def getNextEntitiesAndTUIs(self, entity, list_linked_entities):
        entities_list = []
        TUIs_list = []
        TUIs = []
        if len(list_linked_entities) == 0:
            entities_list = []
            TUIs_list = []
        else:
            CUIs = list_linked_entities[0][1]
            for CUI in CUIs:
                new_entity = self.linker.kb.cui_to_entity[CUI[0]]
                new_entity_name = new_entity.canonical_name
                TUI = new_entity.types
                if str(entity) != str(new_entity_name):
                    entities_list.append(new_entity_name)
                    TUIs_list.append(TUI)

        return entities_list, TUIs_list
    
    def getTUIs(self, entities, entity_list, TUI_list):
        list = []
        for entity in range(len(entities)):
            entity_name = entities[entity]
            index = entity_list.index(entity_name)
            TUIs = TUI_list[index]
            list.append(TUIs)
        return list  