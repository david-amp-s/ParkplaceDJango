from abc import ABC, abstractmethod

class PaymentRepository(ABC):
    @abstractmethod
    def save(self, payment):
        pass