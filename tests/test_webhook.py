import pytest
import json
from unittest.mock import Mock, patch
from app import create_app
from app.models.message_model import MessageModel

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

class TestWebhook:
    
    def test_health_endpoint(self, client):
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['service'] == 'linebot-inspiration'
    
    def test_webhook_missing_signature(self, client):
        response = client.post('/webhook', data='test')
        assert response.status_code == 400
    
    def test_webhook_empty_body(self, client):
        headers = {'X-Line-Signature': 'test-signature'}
        response = client.post('/webhook', headers=headers)
        assert response.status_code == 400
    
    @patch('app.routes.webhook.line_service')
    def test_webhook_success(self, mock_line_service, client):
        mock_line_service.handle_webhook.return_value = True
        
        headers = {'X-Line-Signature': 'test-signature'}
        data = json.dumps({'events': []})
        
        response = client.post('/webhook', data=data, headers=headers)
        assert response.status_code == 200
        
        response_data = json.loads(response.data)
        assert response_data['status'] == 'success'
    
    @patch('app.routes.webhook.line_service')
    def test_webhook_failure(self, mock_line_service, client):
        mock_line_service.handle_webhook.return_value = False
        
        headers = {'X-Line-Signature': 'test-signature'}
        data = json.dumps({'events': []})
        
        response = client.post('/webhook', data=data, headers=headers)
        assert response.status_code == 400

class TestMessageModel:
    
    def test_message_creation(self):
        message = MessageModel(
            user_id='test_user',
            message_type='text',
            content='Test message #test #example'
        )
        
        assert message.user_id == 'test_user'
        assert message.message_type == 'text'
        assert message.content == 'Test message #test #example'
        assert 'test' in message.tags
        assert 'example' in message.tags
        assert message.is_valid()
    
    def test_message_validation(self):
        # Valid message
        valid_message = MessageModel(
            user_id='user123',
            message_type='text',
            content='Valid content'
        )
        assert valid_message.is_valid()
        
        # Invalid message - empty user_id
        invalid_message1 = MessageModel(
            user_id='',
            message_type='text',
            content='Content'
        )
        assert not invalid_message1.is_valid()
        
        # Invalid message - empty content
        invalid_message2 = MessageModel(
            user_id='user123',
            message_type='text',
            content=''
        )
        assert not invalid_message2.is_valid()
    
    def test_tag_extraction(self):
        message = MessageModel(
            user_id='test',
            message_type='text',
            content='This has #multiple #tags and #duplicates #multiple'
        )
        
        # Should extract unique tags
        assert len(message.tags) == 3
        assert 'multiple' in message.tags
        assert 'tags' in message.tags
        assert 'duplicates' in message.tags
    
    def test_content_processing(self):
        message = MessageModel(
            user_id='test',
            message_type='text',
            content='  Text   with   extra   spaces  \n\r  '
        )
        
        # Should clean up whitespace
        assert message.processed_content == 'Text with extra spaces'
    
    def test_sheets_row_format(self):
        message = MessageModel(
            user_id='test_user',
            message_type='text',
            content='Test content #tag1 #tag2'
        )
        
        row = message.to_sheets_row()
        
        assert len(row) == 6
        assert row[1] == 'text'  # message_type
        assert row[2] == 'Test content #tag1 #tag2'  # content
        assert row[3] == 'test_user'  # user_id
        assert 'tag1, tag2' in row[4] or 'tag2, tag1' in row[4]  # tags
        assert row[5] == 'processed'  # status

if __name__ == '__main__':
    pytest.main([__file__])