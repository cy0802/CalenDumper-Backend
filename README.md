# CalenDumper Backend
> project of Meichu Hackathon 2024

## Introduction
CalenDumper is an diary app that integrates Google Calendar and Gemini. It allows users to leave their thoughts and pictures for each events on Google Calendar. Inspired by the concept of photo dump, we made Gemini generate a weekly dump and a piece of text to summarize a week for users.

This repository is the backend of CalenDumper, which is developed with Flask. 

## How to use it
1. install dependency management package, poetry
2. use `poetry install` to install necessary package
3. copy .env.sample, rename it to .env, and fill out the environmental variables
4. run `python3 app.py` in poetry virtual environment