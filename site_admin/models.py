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

class AboutUs(models.Model):
    """
    Modelo para a seção "Sobre Nós" na página inicial
    """
    mission = models.TextField(
        "Nossa Missão",
        help_text="Texto que descreve a missão da empresa"
    )
    is_active = models.BooleanField(
        "Ativo",
        default=True,
        help_text="Marque para exibir esta seção no site"
    )

    class Meta:
        verbose_name = "Sobre Nós"
        verbose_name_plural = "Sobre Nós"

    def __str__(self):
        return "Configurações Sobre Nós"

    def save(self, *args, **kwargs):
        # Garante que só exista uma instância deste modelo
        self.id = 1
        super().save(*args, **kwargs)


class AboutEducenter(models.Model):
    """
    Modelo para a seção "Sobre o Educenter" na página inicial
    """
    title = models.CharField(
        "Título",
        max_length=200,
        default="Sobre o Educenter"
    )
    content = models.TextField(
        "Conteúdo",
        help_text="Texto principal sobre o Educenter"
    )
    is_active = models.BooleanField(
        "Ativo",
        default=True,
        help_text="Marque para exibir esta seção no site"
    )

    class Meta:
        verbose_name = "Sobre o Educenter"
        verbose_name_plural = "Sobre o Educenter"

    def __str__(self):
        return self.title


class FeatureItem(models.Model):
    """
    Modelo para os itens de características (checkboxes) na seção Sobre o Educenter
    """
    about_section = models.ForeignKey(
        AboutEducenter,
        on_delete=models.CASCADE,
        related_name="feature_items"
    )
    text = models.TextField(
        "Texto do item",
        help_text="Texto que aparecerá com o checkbox"
    )
    order = models.PositiveIntegerField(
        "Ordem",
        default=0,
        help_text="Ordem de exibição dos itens"
    )

    class Meta:
        verbose_name = "Item de Característica"
        verbose_name_plural = "Itens de Característica"
        ordering = ['order']

    def __str__(self):
        return f"Item {self.order} - {self.text[:50]}..."