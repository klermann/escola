from django.db import models

class FeatureBlock(models.Model):
    ICON_CHOICES = [
        ('ti-book', 'Livro'),
        ('ti-blackboard', 'Quadro'),
        ('ti-agenda', 'Agenda'),
        ('ti-write', 'Escrever'),
    ]
    
    icon = models.CharField(
        "Ícone", 
        max_length=50, 
        choices=ICON_CHOICES,
        default='ti-book'
    )
    title = models.CharField("Título", max_length=100)
    description = models.TextField("Descrição")
    is_active = models.BooleanField("Ativo", default=True)
    order = models.PositiveIntegerField("Ordem", default=0)

    class Meta:
        verbose_name = "Bloco de Recurso"
        verbose_name_plural = "Blocos de Recursos"
        ordering = ['order']

    def __str__(self):
        return self.title
    
class HeroContent(models.Model):
    title = models.CharField("Título Principal", max_length=200)
    subtitle = models.TextField("Subtítulo")
    button_text = models.CharField("Texto do Botão", max_length=50)
    button_link = models.CharField("Link do Botão", max_length=200, default='#')
    
    class Meta:
        verbose_name = "Conteúdo do Hero"
        verbose_name_plural = "Conteúdo do Hero"

    def __str__(self):
        return self.title