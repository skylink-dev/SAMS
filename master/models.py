from django.db import models

class PincodeData(models.Model):
    circlename = models.CharField(max_length=100, blank=True, default="")
    regionname = models.CharField(max_length=100, blank=True, default="")
    divisionname = models.CharField(max_length=100, blank=True, default="")
    officename = models.CharField(max_length=150, blank=True, default="")
    pincode = models.CharField(max_length=10, blank=True, default="")
    officetype = models.CharField(max_length=50, blank=True, default="")
    delivery = models.CharField(max_length=50, blank=True, default="")
    district = models.CharField(max_length=100, blank=True, default="")
    statename = models.CharField(max_length=100, blank=True, default="")
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.officename} ({self.pincode})"



# 🗺️ State Table
class State(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


# 🏙️ District Table (under State)
class District(models.Model):
    name = models.CharField(max_length=100)
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="districts")

    class Meta:
        unique_together = ("name", "state")  # Prevent duplicate districts per state
        ordering = ["state__name", "name"]

    def __str__(self):
        return f"{self.name} ({self.state.name})"


# 🏢 Office Table (under District)
class Office(models.Model):
    name = models.CharField(max_length=150)  # Example: Office Name
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name="offices")
    officetype = models.CharField(max_length=50, blank=True, help_text="E.g., Branch, Franchise, Head Office")
    pincode = models.CharField(max_length=10, blank=True)

    class Meta:
        unique_together = ("name", "district")  # Prevent duplicate office names per district
        ordering = ["district__state__name", "district__name", "name"]

    def __str__(self):
        return f"{self.name} ({self.pincode})"
    

class TaskCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default="No description")

    class Meta:
        verbose_name = "Task Category"
        verbose_name_plural = "Task Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name