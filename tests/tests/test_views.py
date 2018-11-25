

def test_pagination_in_view(client):
    response = client.get('/events/')
    assert response.status_code == 200
