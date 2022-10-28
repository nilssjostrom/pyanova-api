from AnovaCooker import AnovaCooker
import appdaemon.plugins.hass.hassapi as hass
import datetime




class AnovaControl(hass.Hass):
 
  def initialize(self): 
    self.listen_state(self.setAnova,self.args["triggerID"], new="on")
    self.listen_state(self.startAnova,"input_button.anova_start")
    self.listen_state(self.stopAnova,"input_button.anova_stop")


    time = datetime.time(0, 0, 0)

    self.run_minutely(self.action, time)

    self.log("AnovaControl initialized")
    
  def action(self, kwargs):
    cooker = AnovaCooker('')
    authenticated = cooker.authenticate('email@example.com', 'xxxx')
    cooker.update_state()
    
    if authenticated:
      water_temp = cooker.water_temp

      #self.log(water_temp)
      target_temp = cooker.target_temp
      #self.log(target_temp)
      water_level_low = cooker.water_level_low
      #self.log(water_level_low)
      #time_remaining = cooker.job_time_remaining / 60
      #self.log(time_remaining)
      self.cook = cooker.cook
      #self.log(cooker.cook)
      self.set_value("input_number.anova_temp", water_temp)
      self.set_value("input_number.anova_target", target_temp)
      if water_level_low:
        self.turn_on("input_boolean.water_low")
      else:
        self.turn_off("input_boolean.water_low")
  def setAnova(self, entity, attribute, old, new, kwargs):

    cooker = AnovaCooker('')
    authenticated = cooker.authenticate('email@example.com', 'xxxx')
    if authenticated:
      cooker.update_state()
      #cooker.cook_time = 60 * 60 * 2 # 2 hours in seconds
      #cooker.target_temp = int(self.args("input_number.set_anova_temp"))
      #state = self.get_state(self.set_anova_temp)
      self.adapi = self.get_ad_api()
      self.set_anova_target = self.adapi.get_state("input_number.set_anova_target") 
      #self.log(self.set_anova_target)
      cooker.target_temp = float(self.set_anova_target)
      if cooker.cook:
        self.turn_on("input_boolean.anova_cooking")
      else:
        self.turn_off("input_boolean.anova_cooking")

      #self.set_anova_time = self.adapi.get_state("input_number.set_anova_time")
      #cooker.cook_time = round(int(float(self.set_anova_time)))/60
      #cooker.cook_time = 7200
      if cooker.save():
        self.set_value("input_number.anova_target", float(self.set_anova_target))
        self.turn_off("input_boolean.test")

  def startAnova(self, entity, attribute, old, new, kwargs):
    cooker = AnovaCooker('')
    authenticated = cooker.authenticate('email@example.com', 'xxxx')
    cooker.cook = True
    #cooker.save()
    self.log("Turning on Anova")
    if cooker.save():
        self.turn_on("input_boolean.anova_cooking")


  def stopAnova(self, entity, attribute, old, new, kwargs):
    cooker = AnovaCooker('')
    authenticated = cooker.authenticate('email@example.com', 'xxxx')
    cooker.cook = False
    #cooker.save()
    self.log("Turning off Anova")
    if cooker.save():
        self.turn_off("input_boolean.anova_cooking")


  
