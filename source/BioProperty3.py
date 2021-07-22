import math
import csv

import Common
import Timer
import Agent
import Activity
import Global

BIOPROPERTY = {
"Hunger" : Common.BIOLOGICAL_PROPERTY_HUNGER,
"Dirty" : Common.BIOLOGICAL_PROPERTY_DIRTY,
"Thirst" : Common.BIOLOGICAL_PROPERTY_THIRSTY,
"Defecate" : Common.BIOLOGICAL_PROPERTY_DEFECATE,
"Urinate" : Common.BIOLOGICAL_PROPERTY_URINATE,
"Energy" : Common.BIOLOGICAL_PROPERTY_ENERGY,
"Exhausted" : Common.BIOLOGICAL_PROPERTY_TIRED,
"Sleepy" : Common.BIOLOGICAL_PROPERTY_SLEEPY,
}

def Fmt(val):
	return "{:.3f}".format(val)

class BioProperty():
	def __init__(self, agent, type, rate, current):
		self.m_agent = agent
		self.m_type = type
		self.m_rate = rate
		self.m_relatedActivity = None
		self.m_relatedActivityId = []
		self.m_currentScore = current
	
	def TryTriggerRelatedActivity(self):
		activityToTrigger = ""
		for actId in self.m_relatedActivityId:
			activity = self.m_agent.GetActivityById(actId)
			if activity != None and activity.CanStart():
				activityToTrigger = actId
				break
		Global.Logger.LogDebug("try trigger "+activityToTrigger)
		
		if activityToTrigger != "":
			self.m_relatedActivity = self.m_agent.TryTrigger(activityToTrigger)
	
	def PrintProperty(self):
		pass
	
	def ProcessOutput(self):
		return []

class Hunger(BioProperty):
	def __init__(self, agent, type, rate, current, habit, effect):
		BioProperty.__init__(self, agent, type, rate, current)
		self.m_habit = habit
		self.m_effect = effect
		self.m_totalScore = current
		self.m_currentEffectScore = 0
		self.m_pointEffect = 0
		self.m_mlUrinate = 0
		self.m_pointHunger = 0
		self.m_relatedActivityId = ["MK2", "MK4", "MK6", "MK"]
	
	def CalculateScore(self):
		self.m_currentScore = self.m_totalScore + self.m_currentEffectScore - self.m_rate[Common.AGENT_ASLEEP if self.m_agent.IsAsleep() else Common.AGENT_AWAKE]
	
	def PostUpdateActivityCalculation(self):
		self.m_totalScore = max(0,(self.m_currentScore - (self.m_rate[Common.AGENT_ASLEEP if self.m_agent.IsAsleep() else Common.AGENT_AWAKE] * self.m_agent.GetEmotionalFactor()) - self.m_agent.GetActivityEffect(self.m_type)))
		self.m_pointHunger = Common.clamp((12 * ( 1 - (self.m_totalScore / self.m_rate[Common.RATE_BASE]) )),0,10)
		self.m_pointEffect = self.m_currentEffectScore / self.m_effect[Common.EFFECT_HABIT_HABIT][Common.EFFECT_NEW_VALUE] * 10
		self.m_mlUrinate = 5 * self.m_pointEffect
		self.m_currentEffectScore = self.CalculateEffect()
	
	def CalculateEffect(self):
		Global.Logger.LogDebug("hunger "+str(self.IsHabit(Timer.GetInstance().GetHour()))+" "+str(self.m_totalScore)+" "+str(self.m_effect[Common.EFFECT_HABIT_NONHABIT][Common.EFFECT_NEW_LIMIT])+" "+str((self.m_totalScore > self.m_effect[Common.EFFECT_HABIT_NONHABIT][Common.EFFECT_NEW_LIMIT])))
		index = Common.EFFECT_HABIT_NONHABIT if ((not self.IsHabit(Timer.GetInstance().GetHour())) or (self.m_totalScore < self.m_effect[Common.EFFECT_HABIT_NONHABIT][Common.EFFECT_NEW_LIMIT])) else Common.EFFECT_HABIT_HABIT
		if self.m_relatedActivity == None and self.m_totalScore < self.m_effect[index][Common.EFFECT_NEW_LIMIT]:
			self.TryTriggerRelatedActivity()
		if (self.m_relatedActivity != None and self.m_relatedActivity.IsRunning()):
			if self.m_currentEffectScore != 0:
				return self.m_currentEffectScore
			return self.m_effect[index][Common.EFFECT_NEW_VALUE] / self.m_relatedActivity.m_duration
		return 0
	
	def GetScore(self):
		return self.m_pointHunger
	
	def IsHabit(self, time):
		if self.m_habit == None:
			return False
		return self.m_habit[time]
	
	def PrintProperty(self):
		# pass
		Global.Logger.LogDebug(self.m_type+" "+Fmt(self.m_currentScore)+" "+Fmt(self.m_rate[Common.AGENT_ASLEEP if self.m_agent.IsAsleep() else Common.AGENT_AWAKE])+" "+Fmt(self.m_agent.GetActivityEffect(self.m_type))+" "+Fmt(self.m_agent.GetEmotionalFactor())+" "+Fmt(self.m_totalScore)+" "+("K" if self.IsHabit(Timer.GetInstance().GetHour()) else "-")+" "+Fmt(self.m_currentEffectScore)+" "+Fmt(self.m_mlUrinate)+" "+Fmt(self.m_pointHunger)+"\n")

class Thirst(BioProperty):
	def __init__(self, agent, type, rate, current, habit, effect):
		BioProperty.__init__(self, agent, type, rate, current)
		self.m_habit = habit
		self.m_effect = effect
		self.m_totalScore = current
		self.m_currentEffectScore = 0
		self.m_mlUrinate = 0
		self.m_relatedActivityId = ["MN4"]
		
	def CalculateScore(self):
		self.m_currentScore = self.m_totalScore - self.m_currentEffectScore + self.m_rate[Common.AGENT_ASLEEP if self.m_agent.IsAsleep() else Common.AGENT_AWAKE]
	
	def CalculateEffect(self):
		if self.m_agent.GetProperty("Hunger").m_relatedActivity != None:
			return (self.m_effect[Common.EFFECT_HABIT_NONHABIT][Common.EFFECT_NEW_VALUE] if self.m_totalScore > self.m_effect[Common.EFFECT_EAT][Common.EFFECT_NEW_LIMIT] else self.m_effect[Common.EFFECT_EAT][Common.EFFECT_NEW_VALUE]) / self.m_agent.GetProperty("Hunger").m_relatedActivity.m_duration * self.m_agent.GetActivityById(self.m_relatedActivityId[0]).m_duration
		
		index = Common.EFFECT_HABIT_HABIT if self.IsHabit(Timer.GetInstance().GetHour()) else Common.EFFECT_HABIT_NONHABIT
		#print("rolade "+str(self.m_relatedActivity)+" "+Fmt(self.m_totalScore)+" "+Fmt(self.m_effect[index][Common.EFFECT_NEW_LIMIT]))
		if self.m_relatedActivity == None and self.m_totalScore >= self.m_effect[index][Common.EFFECT_NEW_LIMIT]:
			#print("TARIGAX")
			self.TryTriggerRelatedActivity()
		
		if (self.m_relatedActivity != None and self.m_relatedActivity.IsRunning()):
			return self.m_effect[index][Common.EFFECT_NEW_VALUE] / self.m_relatedActivity.m_duration
		
		return 0
	
	def PostUpdateActivityCalculation(self):
		self.m_totalScore = Common.clamp((self.m_currentScore + (self.m_rate[Common.AGENT_ASLEEP if self.m_agent.IsAsleep() else Common.AGENT_AWAKE] * self.m_agent.GetEmotionalFactor()) + self.m_agent.GetActivityEffect(self.m_type)),0,10)
		self.m_mlUrinate = 15 * self.m_currentEffectScore
		self.m_currentEffectScore = self.CalculateEffect()
	
	def IsHabit(self, time):
		if self.m_habit == None:
			return False
		return self.m_habit[time]
	
	def GetScore(self):
		return self.m_totalScore
		
	def PrintProperty(self):
		# pass
		Global.Logger.LogDebug(self.m_type+" "+Fmt(self.m_currentScore)+" "+Fmt(self.m_rate[Common.AGENT_ASLEEP if self.m_agent.IsAsleep() else Common.AGENT_AWAKE])+" "+Fmt(self.m_agent.GetActivityEffect(self.m_type))+" "+Fmt(self.m_agent.GetEmotionalFactor())+" "+Fmt(self.m_totalScore)+" "+("K" if self.IsHabit(Timer.GetInstance().GetHour()) else "-")+" "+Fmt(self.m_currentEffectScore)+" "+Fmt(self.m_mlUrinate)+"\n")
	
class Dirty(BioProperty):
	def __init__(self, agent, type, rate, current, habit, effect ):
		BioProperty.__init__(self, agent, type, rate, current)
		self.m_habit = habit
		self.m_effect = effect
		self.m_totalScore = current
		self.m_currentEffectScore = 0
		self.m_relatedActivityId = ["MD"]
	
	def CalculateScore(self):
		self.m_currentScore = self.m_totalScore
		self.m_totalScore = max(0,(self.m_currentScore + (self.m_rate[Common.AGENT_ASLEEP if self.m_agent.IsAsleep() else Common.AGENT_AWAKE] * self.m_agent.GetEmotionalFactor()) + self.m_agent.GetActivityEffect(self.m_type) ))
		
	def CalculateEffect(self):
		index = Common.EFFECT_HABIT_NONHABIT if ((not self.IsHabit(Timer.GetInstance().GetHour())) or (self.m_totalScore > self.m_effect[Common.EFFECT_HABIT_NONHABIT][Common.EFFECT_NEW_LIMIT])) else Common.EFFECT_HABIT_HABIT
		if self.m_relatedActivity == None and self.m_totalScore > self.m_effect[index][Common.EFFECT_NEW_LIMIT]:
			self.TryTriggerRelatedActivity()
		if (self.m_relatedActivity != None and self.m_relatedActivity.IsRunning()):
			return self.m_effect[index][Common.EFFECT_NEW_VALUE] / self.m_relatedActivity.m_duration
		return 0
	
	def PostUpdateActivityCalculation(self):
		self.m_currentEffectScore = self.CalculateEffect()
		self.m_totalScore += self.m_rate[Common.AGENT_ASLEEP if self.m_agent.IsAsleep() else Common.AGENT_AWAKE] + self.m_currentEffectScore
		self.m_totalScore = Common.clamp(self.m_totalScore, 0, 10)
	
	def IsHabit(self, time):
		if self.m_habit == None:
			return False
		return self.m_habit[time]
	
	def GetScore(self):
		return self.m_totalScore
	
	def PrintProperty(self):
		# pass
		Global.Logger.LogDebug(self.m_type+" "+Fmt(self.m_currentScore)+" "+Fmt(self.m_rate[Common.AGENT_ASLEEP if self.m_agent.IsAsleep() else Common.AGENT_AWAKE])+" "+Fmt(self.m_agent.GetActivityEffect(self.m_type))+" "+Fmt(self.m_agent.GetEmotionalFactor())+" "+Fmt(self.m_totalScore)+" "+("M" if self.IsHabit(Timer.GetInstance().GetHour()) else "-")+" "+Fmt(self.m_currentEffectScore)+"\n")

class Energy(BioProperty):
	def __init__(self, agent, type, rate, current):
		BioProperty.__init__(self, agent, type, rate, current)
		self.m_scoreActAndEmo = 0
		self.m_eatEffect = 0
		self.m_totalScore = current
		self.m_pointEnergy = Common.clamp(0 if (self.m_totalScore < (self.m_rate[Common.RATE_BASE] / 6)) else (self.m_totalScore * 10 / self.m_rate[Common.RATE_BASE]),0,10)
		self.m_curPointEnergy = 0
	
	def CalculateScore(self):
		self.m_curPointEnergy = self.m_pointEnergy
		self.m_currentScore = self.m_totalScore
		self.m_scoreActAndEmo = self.m_currentScore - (self.m_rate[Common.AGENT_ASLEEP if self.m_agent.IsAsleep() else Common.AGENT_AWAKE] * self.m_agent.GetEmotionalFactor()) + self.m_agent.GetActivityEffect(self.m_type)
		self.m_eatEffect = self.m_agent.GetProperty("Hunger").m_currentEffectScore / 8
		self.m_totalScore = self.m_scoreActAndEmo + self.m_eatEffect + self.m_rate[Common.AGENT_ASLEEP if self.m_agent.IsAsleep() else Common.AGENT_AWAKE]
		
		self.m_pointEnergy = Common.clamp(0 if (self.m_totalScore < (self.m_rate[Common.RATE_BASE] / 6)) else (self.m_totalScore * 10 / self.m_rate[Common.RATE_BASE]),0,10)
	
	def PostUpdateActivityCalculation(self):
		pass
	
	def GetScore(self):
		return self.m_pointEnergy
	
	def PrintProperty(self):
		Global.Logger.LogDebug(self.m_type+" "+Fmt(self.m_currentScore)+" "+Fmt(self.m_rate[Common.AGENT_ASLEEP if self.m_agent.IsAsleep() else Common.AGENT_AWAKE])+" "+Fmt(self.m_agent.GetActivityEffect(self.m_type))+" "+Fmt(self.m_agent.GetEmotionalFactor())+" "+Fmt(self.m_scoreActAndEmo)+" "+Fmt(self.m_eatEffect)+" "+Fmt(self.m_totalScore)+" "+Fmt(self.m_pointEnergy)+"\n")

class Exhausted(BioProperty):
	def __init__(self, agent, type, rate, current):
		BioProperty.__init__(self, agent, type, rate, current)
		self.m_totalScore = current
		self.m_scoreActAndEmo = 0
		self.m_specialEffect = 0
	
	def CalculateScore(self):
		self.m_currentScore = self.m_totalScore
		self.m_scoreActAndEmo = self.m_currentScore + (self.m_rate[Common.AGENT_ASLEEP if self.m_agent.IsAsleep() else Common.AGENT_AWAKE] * self.m_agent.GetEmotionalFactor()) + self.m_agent.GetActivityEffect(self.m_type)
		self.m_specialEffect = 10 - ((self.m_scoreActAndEmo + self.m_agent.GetProperty("Energy").m_curPointEnergy) / 2)
		self.m_totalScore = self.m_specialEffect + self.m_rate[Common.AGENT_ASLEEP if self.m_agent.IsAsleep() else Common.AGENT_AWAKE]
		
		self.m_totalScore = Common.clamp(self.m_totalScore,0,10)
		
	def PostUpdateActivityCalculation(self):
		pass
	
	def GetScore(self):
		return self.m_totalScore
	
	def PrintProperty(self):
		Global.Logger.LogDebug("Exhausted"+" "+Fmt(self.m_currentScore)+" "+Fmt(self.m_rate[Common.AGENT_ASLEEP if self.m_agent.IsAsleep() else Common.AGENT_AWAKE])+" "+Fmt(self.m_agent.GetActivityEffect(self.m_type))+" "+Fmt(self.m_agent.GetEmotionalFactor())+" "+Fmt(self.m_scoreActAndEmo)+" "+Fmt(self.m_specialEffect)+" "+Fmt(self.m_totalScore)+"\n")
	
class Sleepy(BioProperty):
	def __init__(self, agent, type, rate, current, habit):
		BioProperty.__init__(self, agent, type, rate, current)
		self.m_habit = habit
		self.m_scoreActAndEmo = 0
		self.m_specialEffect = 0
		self.m_totalScore = current
		self.m_relatedActivityId = ["TDM", "TD"]
		self.m_curRate = 0
	
	def CalculateScore(self):
		self.m_currentScore = self.m_totalScore
		self.m_scoreActAndEmo = self.m_currentScore + (self.m_rate[Common.AGENT_ASLEEP if self.m_agent.IsAsleep() else Common.AGENT_AWAKE] * self.m_agent.GetEmotionalFactor()) + self.m_agent.GetActivityEffect(self.m_type)
		self.m_specialEffect = self.m_scoreActAndEmo + (self.m_agent.GetProperty("Exhausted").m_currentScore / (8 * Timer.MINUTE_IN_HOUR))
		self.m_curRate = self.m_rate[Common.AGENT_ASLEEP if self.m_agent.IsAsleep() else Common.AGENT_AWAKE]
		self.m_totalScore = self.m_specialEffect + self.m_curRate
		
		self.m_totalScore = Common.clamp(self.m_totalScore,0,10)
		
		if ((self.m_totalScore >= 10) or (self.IsHabit(Common.AGENT_ASLEEP,Timer.GetInstance().GetHour()) and self.m_totalScore > 8)) and self.m_relatedActivity == None:
			self.TryTriggerRelatedActivity()
		# print("sokorento "+str(self.m_totalScore)+" "+str(self.m_curRate)+" "+str(self.m_agent.IsAsleep()))
		if self.m_relatedActivity != None and ((self.m_totalScore <= 1) or (self.IsHabit(Common.AGENT_AWAKE,Timer.GetInstance().GetHour()) and self.m_totalScore <= 2)):
			self.m_relatedActivity.ForceStop()
	
	def IsHabit(self, index, time):
		return self.m_habit[index][time]
		
	def PostUpdateActivityCalculation(self):
		pass
	
	def GetScore(self):
		return self.m_totalScore
	
	def PrintProperty(self):
		Global.Logger.LogDebug(self.m_type+" "+Fmt(self.m_currentScore)+" "+Fmt(self.m_curRate)+" "+Fmt(self.m_agent.GetActivityEffect(self.m_type))+" "+Fmt(self.m_agent.GetEmotionalFactor())+" "+Fmt(self.m_scoreActAndEmo)+" "+Fmt(self.m_specialEffect)+" "+Fmt(self.m_totalScore) + " "+ ("KT" if self.IsHabit(Common.AGENT_ASLEEP,Timer.GetInstance().GetHour()) else ("KB" if self.IsHabit(Common.AGENT_AWAKE,Timer.GetInstance().GetHour()) else "-"))+" "+("T" if self.m_agent.IsAsleep() else "B")+"\n")

class Defecate(BioProperty):
	def __init__(self, agent, type, habit, rule, inStomach, clepPressure):
		BioProperty.__init__(self, agent, type, None, 0)
		self.m_habit = habit
		self.m_inStomach = inStomach
		self.m_clepPressure = clepPressure
		self.m_inIntestine = 0
		self.m_inColon = 0
		self.m_rateStomachToIntestine = 0
		self.m_tick = 0
		self.m_tickStart = False
		self.m_inColonEdge = 0
		self.m_gotoRectom = 0
		self.m_rule = rule
		self.m_eatEffect = 0
		self.m_rateIntestineToColon = 0
		self.m_agent = agent
		self.K_COLUMN_NAME = ["DEFEKASI", "Efek Makan", "Ada di Lambung", "Laju Lambung ke Usus Halus", "Ada di Usus Halus", "Laju dari Usus Halus ke Kolon", "Ada di Kolon", "Ada di ujung Kolon", "Laju dari Kolon ke Rektum", "Kebiasaan", "Efek Aktivitas", "Pengaruh Emosi", "Ada di Akhir Kolon Menuju Rektum", "Tekanan ke Klep Rektum", "Tingkat Defekasi Terkini", "BAB atau Tidak"]
		self.m_effectRemainingTime = 0
		self.K_SIX_HOUR = (6 * Timer.MINUTE_IN_HOUR)
		self.m_prevIntestine = 0
		self.m_toRectum = 0
		self.m_score = 0
		self.m_scorePoint = 0
		self.m_relatedActivityId = ["BAB"]
	
	def CalculateScore(self):
		self.m_eatEffect = self.m_agent.GetProperty("Hunger").m_currentEffectScore
		if self.m_eatEffect > 0:
			self.m_rateStomachToIntestine = (self.m_eatEffect + self.m_inStomach) / ((self.K_SIX_HOUR * 2) if self.m_agent.IsAsleep() else self.K_SIX_HOUR)
			#self.m_tickStart = True
		self.m_inStomach = max(self.m_inStomach + self.m_eatEffect - self.m_rateStomachToIntestine ,0)
		if self.m_inStomach == 0:
			self.m_rateStomachToIntestine = 0
		self.m_prevIntestine = self.m_inIntestine
		self.m_inIntestine += (self.m_rateStomachToIntestine / ((self.K_SIX_HOUR * 2) if self.m_agent.IsAsleep() else self.K_SIX_HOUR)) if self.m_inStomach >= 0 else (-self.m_rateIntestineToColon)
		self.m_inIntestine = max(0,self.m_inIntestine)
		# self.m_inIntestine += (self.m_rateStomachToIntestine - (self.m_rateIntestineToColon if self.m_tick >= self.K_SIX_HOUR else 0)) if self.m_inStomach > 0 else -(self.m_rateIntestineToColon if self.m_tick >= self.K_SIX_HOUR else 0)
		# self.m_inIntestine += (self.m_rateStomachToIntestine  - self.m_rateIntestineToColon)
	
		# if self.m_eatEffect > 0:
		# if self.m_inIntestine == 0:
			# self.m_rateIntestineToColon = 0
		# else:
		self.m_rateIntestineToColon = ((self.m_prevIntestine + self.m_eatEffect) / ((6 * 2) if self.m_agent.IsAsleep() else 6)) if self.m_eatEffect > 0 else (self.m_rateIntestineToColon if self.m_inIntestine > 0 else 0 )
		
		self.m_inColon = (self.m_inColonEdge - ((self.m_rateToRectum if self.IsHabit(Timer.GetInstance().GetHourForTime(Timer.GetInstance().m_time - 1)) else 453.592) * 5 / self.m_relatedActivity.m_duration)) if (self.m_relatedActivity != None) else ((self.m_inColonEdge + self.m_rateIntestineToColon) if (self.m_inIntestine > 0) else ((self.m_inColonEdge - self.m_rateToRectum) if self.m_inColonEdge > 0 else 0))
		self.m_inColonEdge = (self.m_inColon + (self.m_rateIntestineToColon / 24)) if self.m_agent.m_wasAsleep else (self.m_inColon + (self.m_rateIntestineToColon / 12) - (0 if (self.m_relatedActivity == None) else (453.592 / self.m_relatedActivity.m_duration)))
		
		
		
		
		# self.m_inColonEdge = (self.m_inColon - (self.m_inColon / (3 * (1 if Timer.GetInstance().m_format == Common.FORMAT_TIME_HOUR else self.m_duration)))) if self.m_relatedActivity != None else self.m_inColon
		self.m_rateToRectum = self.m_inColonEdge * 0.15
		self.m_toRectum = self.m_rateToRectum / 12
		
		calc1 = (self.m_score / 8 + self.m_clepPressure + self.m_agent.GetActivityEffect(self.m_type)) * self.m_agent.GetEmotionalFactor()
		
		self.m_score = (self.m_clepPressure * self.m_agent.GetEmotionalFactor() )if (self.m_agent.m_wasAsleep) else ((self.m_score / 12 + self.m_clepPressure + self.m_agent.GetActivityEffect(self.m_type))if (self.m_relatedActivity == None) else ((calc1 - ((27.539 if calc1 >= 23.955 else 23.955)/self.m_relatedActivity.m_duration)) if self.IsHabit(Timer.GetInstance().GetHourForTime(Timer.GetInstance().m_time - 1)) else (calc1 - ((31.143 if calc1 >= 28.747 else 28.747)/self.m_relatedActivity.m_duration))))
		self.m_clepPressure = (self.m_toRectum * 0.7355)
		
		
		# self.m_score = (((self.m_clepPressure + self.m_agent.GetActivityEffect(self.m_type)) * self.m_agent.GetEmotionalFactor()) - ((self.m_rule[Common.EFFECT_HABIT_HABIT] if self.IsHabit(Timer.GetInstance().GetHour()) else self.m_rule[Common.EFFECT_HABIT_NONHABIT]) if self.m_relatedActivity != None else 0))
		
		self.m_score = max(0,self.m_score)
		
		self.m_scorePoint = self.m_score * 10 / 28.747
		
	def GetScore(self):
		return self.m_scorePoint
		
	def PostUpdateActivityCalculation(self):
		if (not self.m_agent.IsAsleep()):
			if (self.m_relatedActivity == None) and (self.m_score > (23.955 if self.IsHabit(Timer.GetInstance().GetHour()) else 28.747)):
				self.TryTriggerRelatedActivity()
	
	def IsHabit(self, time):
		if self.m_habit == None:
			return False
		return self.m_habit[time]
	
	def PrintProperty(self):
		# pass
		Global.Logger.LogDebug(self.m_type+" "+Fmt(self.m_eatEffect)+" "+Fmt(self.m_inStomach)+" "+Fmt(self.m_rateStomachToIntestine)+" "+Fmt(self.m_inIntestine)+" "+Fmt(self.m_rateIntestineToColon)+" "+Fmt(self.m_inColon)+" "+Fmt(self.m_inColonEdge)+" "+Fmt(self.m_rateToRectum)+" "+("K" if self.IsHabit(Timer.GetInstance().GetHour()) else "-")+" "+Fmt(self.m_agent.GetActivityEffect(self.m_type))+" "+Fmt(self.m_agent.GetEmotionalFactor())+" "+Fmt(self.m_toRectum)+" "+Fmt(self.m_clepPressure)+" "+Fmt(self.m_score)+" "+ ("B" if self.m_relatedActivity != None else "T")+" "+Fmt(self.m_scorePoint)+"\n")

class Urinate(BioProperty):
	def __init__(self, agent, type, rate, effect, bodyWater, inBladder, remainingInBladder):
		BioProperty.__init__(self, agent, type, rate, 0)
		self.m_type = type
		self.m_rate /= Timer.MINUTE_IN_HOUR
		self.m_effect = effect
		self.m_bodyWater = bodyWater
		self.m_inBladder = inBladder
		self.m_remainingInBladder = remainingInBladder
		self.m_eatEffect = 0
		self.m_drinkEffect = 0
		self.m_relatedActivityId = ["BAK"]
		self.m_effect[Common.EFFECT_URINATE_NORMAL][Common.EFFECT_NEW_VALUE] /= self.m_agent.GetActivityById(self.m_relatedActivityId[0]).m_duration
		self.m_effect[Common.EFFECT_URINATE_DEFECATE][Common.EFFECT_NEW_VALUE] /= self.m_agent.GetActivityById(self.m_agent.GetProperty("Defecate").m_relatedActivityId[0]).m_duration
		self.m_point = self.m_remainingInBladder / self.m_effect[Common.EFFECT_URINATE_NORMAL][Common.EFFECT_NEW_LIMIT] * 10
		
		# self.m_rate[Common.RATE_TOPEE] /= self.m_agent.GetActivityById(self.m_relatedActivityId[0])
	
	def CalculateScore(self):
		self.m_drinkEffect = self.m_agent.GetProperty("Thirst").m_mlUrinate * 0.2
		self.m_eatEffect = self.m_agent.GetProperty("Hunger").m_mlUrinate * 0.05
		self.m_bodyWater += self.m_drinkEffect + self.m_eatEffect - self.m_rate
		
		self.m_inBladder = self.m_remainingInBladder + (self.m_rate * self.m_agent.GetEmotionalFactor()) + self.m_agent.GetActivityEffect(self.m_type) + (0 if self.m_relatedActivity == None else self.m_rate)
		
		if self.m_inBladder > self.m_effect[Common.EFFECT_URINATE_NORMAL][Common.EFFECT_NEW_LIMIT] and self.m_relatedActivity == None:
			self.TryTriggerRelatedActivity()
		# if Timer.GetInstance().m_format == Common.FORMAT_TIME_MINUTE and self.m_inBladder > 10 and not self.m_effectStarted:
			# self.m_effectStarted = True
			# self.m_effectRemainingTime = self.m_duration
	def PostUpdateActivityCalculation(self):
			
		if self.m_relatedActivity != None or (self.m_agent.GetProperty("Defecate").m_relatedActivity != None and self.m_inBladder > self.m_effect[Common.EFFECT_URINATE_NORMAL][Common.EFFECT_NEW_LIMIT]):
			# print("cur")
			self.m_remainingInBladder = self.m_inBladder - self.m_effect[Common.EFFECT_URINATE_NORMAL][Common.EFFECT_NEW_VALUE]
		elif self.m_agent.GetProperty("Defecate").m_relatedActivity != None:
			# print("sing")
			self.m_remainingInBladder = self.m_inBladder - self.m_effect[Common.EFFECT_URINATE_DEFECATE][Common.EFFECT_NEW_VALUE]
		else:
			# print("tep")
			self.m_remainingInBladder = self.m_inBladder
		
		self.m_remainingInBladder = max(0, self.m_remainingInBladder)
		self.m_point = self.m_remainingInBladder / self.m_effect[Common.EFFECT_URINATE_NORMAL][Common.EFFECT_NEW_LIMIT] * 10
	
	def GetScore(self):
		return self.m_point
	
	def PrintProperty(self):
		# pass
		Global.Logger.LogDebug(self.m_type+" "+Fmt(self.m_drinkEffect)+" "+Fmt(self.m_eatEffect)+" "+Fmt(self.m_bodyWater)+" "+Fmt(self.m_rate)+" "+Fmt(self.m_agent.GetActivityEffect(self.m_type))+" "+Fmt(self.m_agent.GetEmotionalFactor())+" "+Fmt(self.m_inBladder)+" "+Fmt(self.m_remainingInBladder)+" "+Fmt(self.m_point)+"\n")