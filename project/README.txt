
##############################  Django JET  ####################################

https://jet.readthedocs.io/en/latest/getting_started.html

Джет - это батарейка для изменения внешнего вида интерфейса админ-панели.
В придачу к нему также установлена дашборд для вывода различных виджетов.

Для кастомизации виджетов дашборда используется класс CustomIndexDashboard
в модуле dashboard.py, расположенному в корне.

! ОСОБЕННОСТИ ПЛАГИНА
1. Официальная версия плагина несовместима с версией Django >= 3.0,
так как из 3.0 вырезали функцию python_2_unicode_compatible, используемую джетом.
Поэтому используется совместимая версия либы от какого-то индуса,
который поправил проблему с импортом: https://github.com/Barukimang/django-jet.

2. Дашборд
 2.1 По умолчанию не работает селектор добавления виджетов вверху.
     Он пытается подхватить jquery, но остается с пустыми руками.
     Поэтому в базовых templates определен шаблон admin/base.html,
     содержащий фикс данного недоразумения.



############################  Экспорт в Excel  #################################

Экспорт реализован в приложении users и orders.

Для экспорта написан общий интерфейс, расположенный в аппке commons.
Чтобы им воспользоваться нужно в файле admin.py унаследовать админ-класс 
from apps.commons.admin import ExportExcelAdmin и указать требуемые атрибуты.


Также создается файл export2xlsx, где создаются два наследника
from apps.commons.export import ExportLimiter, ExportXlsx

ExportLimiter реализует ограничение по экспорту в excel,
по умолчанию раз в 2 минуты.

ExportXlsx реализует создание эксель файла и экспорт его в файл или байтовый массив.



############################  Приложение Content  ##############################

В данном приложении присутсвет блок товаров.
Элементы блока должны содержать внешний ключ на товар.
Возможен вариант, когда нам требуется приложение контента без каталога.
Для этого использован некоторый костыль, при отсутствии каталога модель останется,
 но не будет содержать поля с фк на товар.
content/models - ProductsBlockItem
При попытке сохранения блока через админ панель выйдет уведомление
 о необходимости установки модуля каталог.
Данное ограничение расположено в admin.py



#########################  Сравение и избранные товары #########################

Для сравнения и избранных написаны приложения compare и wishlist.
По структуре кода они очень схожи, но если написать общие базовые классы,
то хер знает где их хранить.
1. Если в отдельном приложении, то они перестанут быть модульными и будут
зависеть от него.
2. Если в приложении commons, то их реализация будет всегда доступна.
 т.е. если передаем клиенту код проекта, а в услуги не входили избранные и сравнение,
 то он получает и базовую реализизацию этого функционала, тоже не очень хорошо.
3. Если объединить в отдельное приложение, то получаем аналогичную ситуацию
 как в пункте 2, только с одним из функционалов.
