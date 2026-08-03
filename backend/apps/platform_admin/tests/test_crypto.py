from apps.platform_admin.crypto import decrypt_secret, encrypt_secret


def test_encrypt_decrypt_roundtrip():
    ciphertext = encrypt_secret("sk-ant-super-secret-value")
    assert ciphertext != "sk-ant-super-secret-value"
    assert decrypt_secret(ciphertext) == "sk-ant-super-secret-value"


def test_ciphertext_does_not_contain_plaintext_substring():
    secret = "sk-ant-do-not-leak-me"
    ciphertext = encrypt_secret(secret)
    assert secret not in ciphertext
