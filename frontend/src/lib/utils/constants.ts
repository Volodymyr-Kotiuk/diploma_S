export const helperText: Record<string, string> = {
  cpu_saturation:
    'Стан, коли процесорні ресурси вузла майже повністю використані, що може спричинити затримки сервісів.',
  memory_pressure:
    'Стан, коли оперативної пам’яті недостатньо і система починає використовувати swap.',
  disk_io_bottleneck:
    'Обмеження продуктивності через повільні або перевантажені дискові операції.',
  resource_overcommit:
    'Ситуація, коли віртуальним вузлам виділено більше ресурсів, ніж реально доступно фізично.',
  underutilization:
    'Ситуація, коли вузол тривалий час використовує дуже малу частку виділених ресурсів.',
  scaling_recommendation:
    'Обґрунтована порада щодо збільшення, зменшення або перерозподілу ресурсів.'
};

export const scenarioLabels: Record<string, string> = {
  cpu_saturation: 'Перевантаження CPU',
  memory_pressure: 'Нестача пам’яті',
  swap_pressure: 'Навантаження підкачки',
  disk_io_bottleneck: 'Обмеження дискових операцій',
  network_pressure: 'Навантаження мережі',
  resource_overcommit: 'Перевиділення ресурсів',
  underutilization: 'Недовикористання ресурсів',
  thermal_risk: 'Температурний ризик',
  mixed_resource_degradation: 'Змішана деградація ресурсів'
};
