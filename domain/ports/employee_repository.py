from abc import ABC, abstractmethod

class EmployeeRepository(ABC):

    @abstractmethod
    def get_all(self):
        pass

    @abstractmethod
    def get_by_id(self, employee_id):
        pass

    @abstractmethod
    def create(self, employee):
        pass

    @abstractmethod
    def delete(self, employee_id):
        pass

    @abstractmethod
    def find_by_username(self,username): 
        pass