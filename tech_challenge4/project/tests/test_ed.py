from project.source.extraction import DataExtractor
from project.source.transformation import Transformer

def get_data_extractor_instance():
    req = DataExtractor(symbol='NTDOY', period='1w')
    result = req.get_data()
    print(f'result: {result}')
    return 'success' if result is not None else 'failure'

def transformate_data_extractor_instance():
    return Transformer.normalize_data()

def test_data_engineering():
    result = get_data_extractor_instance()
    if result == 'success':
        transformate_data_extractor_instance()
    assert result == 'success'
    
if __name__ == "__main__":
    test_data_engineering()